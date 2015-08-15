#!/bin/env python

import os
import re
import argparse

from fannsdb.cmdhelper import DefaultCommandHelper
from fannsdb.utils import RatedProgress

def main():
	parser = argparse.ArgumentParser(
		description="Map score values")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	cmd.add_transform_args()

	parser.add_argument("--skip-empty-scores", dest="skip_empty_scores", action="store_true", default=False,
						help="Skip transformation for empty scores")

	args, logger = cmd.parse_args("scores-transform")

	db = cmd.open_db()

	try:
		transforms = cmd.get_transforms()

		predictors = transforms.keys()

		logger.info("Transforming scores ...")

		progress = RatedProgress(logger, name="SNVs")

		rows_count = updated_count = 0
		for row in db.query_scores(predictors=predictors):
			rows_count += 1

			scores = row["scores"]
			upd_scores = {}

			for predictor in transforms:
				score = scores[predictor]
				if args.skip_empty_scores and score is None:
					continue

				prev_score = score
				for name, func in transforms[predictor]:
					try:
						score = func(score)
					except:
						raise Exception("Error transforming the {} score {} with {}".format(predictor, score, name))

				if prev_score != score:
					upd_scores[predictor] = score

			if len(upd_scores) > 0:
				db.update_scores(row["id"], upd_scores)
				updated_count += 1

			progress.update()

		progress.log_totals()

		logger.info("Commit ...")

		db.commit()

		logger.info("Finished. Total rows = {}, updated rows = {}, elapsed time = {}".format(rows_count, updated_count, progress.elapsed_time))
	except:
		return cmd.handle_error()
	finally:
		db.close()

	return 0

if __name__ == "__main__":
	exit(main())
