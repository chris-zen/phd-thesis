#!/usr/bin/env python

import time
import argparse

from bgcore import logging as bglogging
from fannsdb.db.sqlitedb import FannsSQLiteDb
from fannsdb.utils import hsize
from condel._DEPRECATED_.weights import load_weights


def main():
	parser = argparse.ArgumentParser(
		description="Calculate Condel label")

	parser.add_argument("db_path", metavar="DB_PATH",
						help="Functional scores database")

	parser.add_argument("weights_path", metavar="WEIGHTS",
						help="File containing the scores weights and cutoffs")

	parser.add_argument("-p", "--predictors", dest="predictors", metavar="PREDICTORS",
						help="Comma separated list of predictors")

	parser.add_argument("-u", "--updated-predictors", dest="updated_predictors", metavar="NAMES",
						help="Updated predictor names")

	bglogging.add_logging_arguments(parser)

	args = parser.parse_args()

	bglogging.initialize(args)

	log = bglogging.get_logger("calculate-label")

	log.info("Opening functional scores database ...")

	db = FannsSQLiteDb(args.db_path)
	db.open()

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

	if args.updated_predictors is not None:
		updated_predictors = [p.strip() for p in args.updated_predictors.split(",")]
		if len(predictors) != len(updated_predictors):
			log.error("Number of updated predictors does not match with the list of number of predictors")
			exit(-1)
	else:
		updated_predictors = ["{}_CLASS".format(p.upper()) for p in predictors]

	log.info("Available predictors: {}".format(", ".join(avail_predictors)))
	log.info("Selected predictors: {}".format(", ".join(predictors)))

	for predictor, updated_predictor in zip(predictors, updated_predictors):
		log.info("Creating predictor {} ...".format(updated_predictor))
		db.add_predictor(updated_predictor, FannsDb.CALCULATED_PREDICTOR_TYPE, source=[predictor])

	cutoffs = []
	for predictor in predictors:
		cutoff, mcc, acc = [stats[predictor][v] for v in ["cutoff", "cutoff_mcc", "cutoff_acc"]]
		log.info("{}: cutoff={}, MCC={}, accuracy={}".format(predictor, cutoff, mcc, acc))
		cutoffs += [cutoff]

	log.info("Calculating ...")

	start_time = partial_start_time = time.time()
	try:
		for num_rows, row in enumerate(db.query_scores(predictors=predictors), start=1):
			scores = row["scores"]
			d = {}
			for i, predictor in enumerate(predictors):
				score = scores[predictor]
				if score is None:
					continue

				cutoff = cutoffs[i]
				updated_predictor = updated_predictors[i]

				d[updated_predictor] = 0.0 if score < cutoff else 1.0

			db.update_scores(row["id"], d)

			partial_time = time.time() - partial_start_time
			if partial_time > 5.0:
				partial_start_time = time.time()
				elapsed_time = time.time() - start_time
				log.debug("  {} rows, {:.1f} rows/second".format(hsize(num_rows), num_rows / elapsed_time))

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
