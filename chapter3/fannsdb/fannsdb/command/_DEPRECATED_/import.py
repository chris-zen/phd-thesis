#!/bin/env python

import argparse

from bgcore import tsv
from fannsdb.cmdhelper import Command, DbTrait, PredictorsTrait
from fannsdb.utils import RatedProgress
from fannsdb.types import score_value
from fannsdb.columns import COORD_COLUMNS, COORD_TYPES

def main():
	parser = argparse.ArgumentParser(
		description="Import scores into the database")

	cmd = Command.withtraits(DbTrait, PredictorsTrait)(parser)

	cmd.add_db_args()

	parser.add_argument("source_path", metavar="SOURCE",
						help="The source file. Use - for standard input.")

	#TODO: which are the coordinates column

	cmd.add_selected_predictors_args()

	parser.add_argument("--skip-empty-scores", dest="skip_empty_scores", action="store_true", default=False,
						help="Skip SNV's where all the scores are empty")

	parser.add_argument("--skip-update-predictors", dest="skip_update_predictors", action="store_true", default=False,
						help="Skip the update of the predictors.")

	parser.add_argument("--skip-create-index", dest="skip_create_index", action="store_true", default=False,
						help="Skip the creation of the database indices.")

	parser.add_argument("--ignore-errors", dest="ignore_errors", action="store_true", default=False,
						help="When errors on the input file, report them but continue processing the input.")

	args, logger = cmd.parse_args("import")

	db = cmd.open_db()

	try:
		progress = RatedProgress(logger, name="SNVs")

		total_lines = 0

		logger.info("Reading {} ...".format(args.source_path if args.source_path != "-" else "from standard input"))

		with tsv.open(args.source_path) as f:
			# Parse header
			hdr_line = f.readline()
			hdr = {}
			for index, name in enumerate(hdr_line.rstrip("\n").split("\t")):
				hdr[name] = index

			# Predictors to update from the user selection and source availability
			db_predictors = set([p["id"] for p in db.predictors()])
			src_predictors = [name for name in hdr if name not in COORD_COLUMNS]
			predictors = cmd.get_selected_predictors(available_predictors=src_predictors)
			for predictor in predictors:
				if predictor not in db_predictors:
					logger.info("Creating non existing predictor: {}".format(predictor))
					db.add_predictor(predictor, FannsDb.SOURCE_PREDICTOR_TYPE)

			logger.info("Predictors: {}".format(", ".join(predictors)))

			all_columns = COORD_COLUMNS + predictors
			types = COORD_TYPES + ([score_value] * len(predictors))

			missing_columns = [name for name in all_columns if name not in hdr]
			if len(missing_columns) > 0:
				raise Exception("The following columns are missing: {}".format(", ".join(missing_columns)))

			columns = [hdr[name] for name in all_columns]
			max_column = max(columns)

			for line_num, line in enumerate(f, start=2):
				fields = line.rstrip("\n").split("\t")

				if len(fields) < max_column:
					log.error("Missing columns for line {}: {}".format(line_num, " ".join(fields)))
					if not args.ignore_errors:
						raise

				try:
					fields = [type_cast(fields[index]) for type_cast, index in zip(types, columns)]
				except Exception as ex:
					logger.error("{} at line {}: {}".format(str(ex), line_num, " ".join(fields)))
					if not args.ignore_errors:
						raise

				(chr, strand, start, ref, alt, transcript,
				 aa_pos, aa_ref, aa_alt, protein) = fields[:10]

				scores = fields[10:]

				if args.skip_empty_scores and sum([0 if s is None else 1 for s in scores]) == 0:
					continue

				try:
					db.add_snv(
								chr=chr, strand=strand, start=start, ref=ref, alt=alt, transcript=transcript,
								protein=protein, aa_pos=aa_pos, aa_ref=aa_ref, aa_alt=aa_alt,
								scores=dict(zip(predictors, scores)))
				except Exception as ex:
					logger.error("Error importing SNV at line {}: {}".format(line_num, str(ex)))
					if not args.ignore_errors:
						raise

				progress.update()

			total_lines += line_num

		progress.log_totals()

		logger.info("Finalizing database ...")

		if not args.skip_update_predictors:
			logger.info("Updating predictors ...")
			db.update_predictors()

		logger.info("Committing ...")
		db.commit()

		if not args.skip_create_index:
			logger.info("Creating indices ...")
			db.create_indices()

		logger.info("Finished successfully. Elapsed time: {}".format(progress.elapsed_time))

	except:
		return cmd.handle_error()
	finally:
		db.close()

	return 0

if __name__ == "__main__":
	exit(main())
