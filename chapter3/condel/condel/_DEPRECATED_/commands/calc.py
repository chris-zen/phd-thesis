#!/usr/bin/env python

import time
import argparse

from bgcore import logging as bglogging
from fannsdb.db.sqlitedb import FannsSQLiteDb
from fannsdb.utils import hsize
from condel._DEPRECATED_.weights import load_weights


PREDICTOR_TRANSFORM = dict(
	SIFT=lambda v: 1.0 - v,
	MA=lambda v: (v / 12) + 0.5)

def main():
	parser = argparse.ArgumentParser(
		description="Calculate Condel score")

	parser.add_argument("db_path", metavar="DB_PATH",
						help="Functional scores database")

	parser.add_argument("weights_path", metavar="WEIGHTS",
						help="File containing the scores weights and cutoffs")

	parser.add_argument("-p", "--predictors", dest="predictors", metavar="PREDICTORS",
						help="Comma separated list of predictors")

	parser.add_argument("-u", "--updated-predictor", dest="updated_predictor", metavar="NAME",
						help="Updated predictor name")

	bglogging.add_logging_arguments(parser)

	args = parser.parse_args()

	bglogging.initialize(args)

	log = bglogging.get_logger("calculate")

	log.info("Opening functional scores database ...")

	db = FannsSQLiteDb(args.db_path)
	db.open()

	updated_predictor = args.updated_predictor or "CONDEL"

	predictors = set([p["id"] for p in db.predictors()])
	if updated_predictor not in predictors:
		log.info("  Creating predictor {} ...".format(updated_predictor))
		db.add_predictor(updated_predictor, FannsDb.CALCULATED_PREDICTOR_TYPE, source=predictors)

	log.info("Loading state ...")

	state = load_weights(args.weights_path)

	avail_predictors, precision, step, stats = [state[k] for k in ["predictor_names", "precision", "step", "stats"]]
	if args.predictors is not None:
		predictors = [p for p in [p.strip() for p in args.predictors.split(",")] if p in avail_predictors]
		if len(predictors) == 0:
			log.error("Unknown predictors: {}".format(args.predictors))
			log.error("Available predictor names are: {}".format(", ".join(avail_predictors)))
			exit(-1)
	else:
		predictors = avail_predictors

	log.info("Available predictors: {}".format(", ".join(avail_predictors)))
	log.info("Selected predictors: {}".format(", ".join(predictors)))

	log.info("Calculating ...")

	start_time = partial_start_time = time.time()
	try:
		for num_rows, row in enumerate(db.query_scores(predictors=predictors), start=1):
			scores = row["scores"]
			condel = wsum = 0
			for predictor, score in scores.items():
				if score is None:
					continue

				predictor_stats = stats[predictor]
				rmin, rmax, dim, size, cdp, cdn, cutoff = [predictor_stats[k] for k in [
																"rmin", "rmax", "dim", "size", "cdp", "cdn", "cutoff"]]

				if predictor in PREDICTOR_TRANSFORM:
					score = PREDICTOR_TRANSFORM[predictor](score)

				r = (score - rmin) / dim
				index = int(r * size) if score < rmax else size - 1

				if score < cutoff:
					w = 1 - cdn[index]
				else:
					w = 1 - cdp[index]

				wsum += w
				condel += w * score

				#log.info("{}={}, w={} -> {}".format(predictor_name, score, w, score * w))

			if wsum != 0:
				condel /= wsum

				d = {updated_predictor : condel}
				db.update_scores(row["id"], d)

				#log.info(">>> CONDEL={}".format(condel))
			else:
				log.warn("wsum = 0, condel={}, scores={}".format(condel, repr(scores)))

			partial_time = time.time() - partial_start_time
			if partial_time > 5.0:
				partial_start_time = time.time()
				elapsed_time = time.time() - start_time
				log.debug("  {} rows, {:.1f} rows/second".format(hsize(num_rows), num_rows / elapsed_time))

		log.info("Commit ...")
		db.commit()
	except KeyboardInterrupt:
		log.warn("Interrupted by Ctrl-C")
		db.rollback()
	except:
		db.rollback()
		raise
	finally:
		db.close()

if __name__ == "__main__":
	main()
