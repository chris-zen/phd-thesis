#!/usr/bin/env python

import argparse
import json

from bgcore import tsv
from fannsdb.cmdhelper import Command, DbTrait, PredictorsInDbTrait, TransformsTrait
from fannsdb.utils import RatedProgress


def calculate_tfic(predictors, updated_predictors, feature_stats, scores, transforms):
	tfic_scores = {}
	for predictor in predictors:
		upd_pred = updated_predictors[predictor]
		tfic_scores[upd_pred] = None

		pred_stats = feature_stats.get(predictor)

		if pred_stats is None:
			continue

		score = scores[predictor]
		if score is None:
			continue

		if predictor in transforms:
			for name, func in transforms[predictor]:
				try:
					score = func(score)
				except:
					raise Exception("Error transforming the {} score {} with {}".format(predictor, score, name))

		mean, sd = pred_stats["mean"], pred_stats["stdev"]

		tfic_scores[upd_pred] = (score - mean) / sd

	return tfic_scores

def main():
	parser = argparse.ArgumentParser(
		description="Calculate TransFIC for the selected scores")

	cmd = Command.withtraits(DbTrait, PredictorsInDbTrait, TransformsTrait)(parser)

	cmd.add_db_args()

	parser.add_argument("feature_name", metavar="FEATURE_COLUMN",
						help="The column name with the features. It can be transcript, protein or any of the available annotations.")

	parser.add_argument("blt_path", metavar="BLT_PATH",
						help="The baseline tolerance statistics.")

	cmd.add_selected_predictors_args()

	parser.add_argument("-u", "--updated-predictors", dest="updated_predictors", metavar="NAME",
						help="Updated predictor names")

	cmd.add_transform_args()

	args, logger = cmd.parse_args("calc")

	db = cmd.open_db()

	# initialize feature selection

	db_annotations = [a["id"] for a in db.maps()]
	if args.feature_name not in set(["transcript", "protein"] + db_annotations):
		logger.error("Feature name not available in the database: {}".format(args.feature_name))
		logger.error("Available annotations: {}".format(", ".join(db_annotations)))
		exit(-1)

	if args.feature_name.lower() in ["transcript", "protein"]:
		annotations = None
		feature_getter = lambda row: row[args.feature_name]
	else:
		annotations = [args.feature_name]
		feature_getter = lambda row: row["annotations"][args.feature_name]

	# predictors, transforms, and updated_predictors

	predictors = cmd.get_selected_predictors(default_all=True)

	transforms = cmd.get_transforms()

	if args.updated_predictors is not None:
		if len(predictors) != len(args.updated_predictors):
			logger.error("The number of selected predictors does not match the number of predictor names to update")
			exit(-1)
		updated_predictors = dict([(p, u) for p, u in zip(predictors, args.updated_predictors)])
	else:
		updated_predictors = dict([(p, "TFIC_{}".format(p)) for p in predictors])

	# create predictors in the database if required

	db_predictors = set([p["id"] for p in db.predictors()])
	for predictor, updated_predictor in updated_predictors.items():
		if updated_predictor not in db_predictors:
			logger.info("Creating predictor {} ...".format(updated_predictor))
			db.add_predictor(updated_predictor, FannsDb.CALCULATED_PREDICTOR_TYPE, source=[predictor])

	try:
		logger.info("Loading baseline tolerance statistics ...")

		with tsv.open(args.blt_path) as f:
			doc = json.load(f)
			blt_predictors = doc["predictors"]
			features = doc["features"]
			blt_stats = doc["blt"]
			num_predictors = len(blt_predictors)

		logger.info("  Predictors: {}".format(", ".join(blt_predictors)))
		logger.info("  Features: {}".format(len(features)))

		logger.info("Calculating ...")

		progress = RatedProgress(logger, name="SNVs")

		rows_count = updated_count = 0
		for row in db.query_scores(predictors=predictors, maps=annotations):
			rows_count += 1

			scores = row["scores"]

			feature = feature_getter(row)
			if feature not in blt_stats:
				continue

			feature_stats = blt_stats[feature]

			tfic_scores = calculate_tfic(predictors, updated_predictors, feature_stats, scores, transforms)

			if len(tfic_scores) > 0:
				db.update_scores(row["id"], tfic_scores)
				updated_count += 1

			progress.update()

		progress.log_totals()

		logger.info("Commit ...")

		db.commit()

		logger.info("Finished. Total rows = {}, updated rows = {}, elapsed_time = {}".format(rows_count, updated_count, progress.elapsed_time))

	except:
		cmd.handle_error()

	return 0

if __name__ == "__main__":
	exit(main())