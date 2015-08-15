#!/usr/bin/env python

import argparse

from fannsdb.utils import RatedProgress
from fannsdb.cmdhelper import Command, DbTrait, PredictorsInDbTrait
from condel._DEPRECATED_.weights import load_weights


def main():
	parser = argparse.ArgumentParser(
		description="Calculate TransFIC labels")

	cmd = Command.withtraits(DbTrait, PredictorsInDbTrait)(parser)
	
	cmd.add_db_args()
	
	parser.add_argument("cutoffs_path", metavar="CUTOFFS",
						help="File containing the cutoffs")

	cmd.add_selected_predictors_args()

	parser.add_argument("-u", "--updated-predictors", dest="updated_predictors", metavar="NAMES",
						help="Updated predictor names")

	args, logger = cmd.parse_args("calc-label")

	db = cmd.open_db()

	try:
		logger.info("Loading state ...")

		state = load_weights(args.cutoffs_path)

		avail_predictors, stats = [state[k] for k in ["predictors", "stats"]]

		predictors = cmd.get_selected_predictors(default_all=True)
		missing_predictors = [p for p in predictors if p not in set(avail_predictors)]
		if len(missing_predictors) > 0:
			raise Exception("Missing cutoff stats for predictors: {}".format(", ".join(missing_predictors)))

		if args.updated_predictors is not None:
			if len(predictors) != len(args.updated_predictors):
				raise Exception("The number of selected predictors does not match the number of predictor names to update")
			updated_predictors = dict([(p, u) for p, u in zip(predictors, args.updated_predictors)])
		else:
			updated_predictors = dict([(p, "{}_LABEL".format(p)) for p in predictors])

		# create predictors in the database if required

		db_predictors = set([p["id"] for p in db.predictors()])
		for predictor, updated_predictor in updated_predictors.items():
			if updated_predictor not in db_predictors:
				logger.info("Creating predictor {} ...".format(updated_predictor))
				db.add_predictor(updated_predictor, FannsDb.CALCULATED_PREDICTOR_TYPE, source=[predictor])

		cutoffs = {}
		for predictor in predictors:
			cutoff_low_mid, cutoff_mid_high = [stats[predictor][v] for v in ["cutoff_low_mid", "cutoff_mid_high"]]
			logger.info("{}: cutoffs: low_mid={}, mid_high={}".format(predictor, cutoff_low_mid, cutoff_mid_high))
			cutoffs[predictor] = (cutoff_low_mid, cutoff_mid_high)

		logger.info("Calculating ...")

		progress = RatedProgress(logger, name="SNVs")

		for num_rows, row in enumerate(db.query_scores(predictors=predictors), start=1):
			scores = row["scores"]
			uscores = {}
			for predictor in predictors:
				score = scores[predictor]
				if score is None:
					continue

				cutoff_low_mid, cutoff_mid_high = cutoffs[predictor]
				updated_predictor = updated_predictors[predictor]

				uscores[updated_predictor] = 0.0 if score < cutoff_low_mid else 1.0 if score < cutoff_mid_high else 2.0

			if len(uscores) > 0:
				db.update_scores(row["id"], uscores)

			progress.update()

		db.commit()
	except:
		cmd.handle_error()

	return 0

if __name__ == "__main__":
	exit(main())
