#!/bin/env python

import argparse

from bgcore import tsv
from fannsdb.cmdhelper import DefaultCommandHelper
from fannsdb.utils import RatedProgress
from fannsdb.types import score_value
from fannsdb.columns import GENOME_COORD_COLUMNS, GENOME_COORD_COLUMN_TYPE, PROTEIN_COORD_COLUMNS, PROTEIN_COORD_COLUMN_TYPE

def main():
	parser = argparse.ArgumentParser(
		description="Update scores in the database")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	parser.add_argument("source_path", metavar="SOURCE",
						help="The source file. Use - for standard input.")

	cmd.add_selected_predictors_args()

	parser.add_argument("--update-predictors", dest="update_predictors", action="store_true", default=False,
						help="Update of the predictors.")

	parser.add_argument("--ignore-errors", dest="ignore_errors", action="store_true", default=False,
						help="When errors on the input file, report them but continue processing the input.")

	args, logger = cmd.parse_args("update")

	db = cmd.open_db()

	predictors = cmd.get_selected_predictors(check_missing=False)

	try:
		progress = RatedProgress(logger, name="SNVs")

		total_lines = 0

		logger.info("Reading {} ...".format(args.source_path if args.source_path != "-" else "from standard input"))

		with tsv.open(args.source_path) as f:
			# Parse header
			hdr_line = f.readline()
			hdr = dict([(name, index) for index, name in enumerate(hdr_line.rstrip("\n").split("\t"))])

			db_predictors = set([p["id"] for p in db.predictors()])

			if len(predictors) == 0:
				predictors = [name for name in hdr if name in db_predictors]
				if len(predictors) == 0:
					raise Exception("Any input file header match the available predictors in the database. Please specify them using -p.")

			logger.info("Predictors: {}".format(", ".join(predictors)))

			for predictor in filter(lambda p: p not in db_predictors, predictors):
				logger.info("Creating predictor {} ...".format(predictor))
				db.add_predictor(predictor, FannsDb.SOURCE_PREDICTOR_TYPE)

			use_genome_coords = len(set(hdr.keys()) & set(GENOME_COORD_COLUMNS)) > 0
			use_protein_coords = len(set(hdr.keys()) & set(PROTEIN_COORD_COLUMNS)) > 0

			if not use_genome_coords and not use_protein_coords:
				raise Exception("No coordinate columns found. "
								"Use {} for genomic coordinates or {} for protein coordinates.".format(
									GENOME_COORD_COLUMNS, PROTEIN_COORD_COLUMNS))
			elif use_genome_coords and use_protein_coords:
				logger.warn("Both, genomic and protein coordinates columns found. Using genomic coordinates by default")

			if use_genome_coords:
				coord_column_names = [n for n in hdr if n in set(GENOME_COORD_COLUMNS)]
				coord_column_types = [GENOME_COORD_COLUMN_TYPE[n] for n in coord_column_names]
				#get_rows = db.get_transcripts_by_dna
			elif use_protein_coords:
				coord_column_names = [n for n in hdr if n in set(PROTEIN_COORD_COLUMNS)]
				coord_column_types = [PROTEIN_COORD_COLUMN_TYPE[n] for n in coord_column_names]
				#get_rows = db.get_transcripts_by_protein

			coord_column_indices = [hdr[n] for n in coord_column_names]
			score_indices = [hdr[n] for n in predictors]
			max_column_index = max(coord_column_indices + score_indices)

			for line_num, line in enumerate(f, start=2):
				fields = line.rstrip("\n").split("\t")

				if len(fields) < max_column_index:
					log.error("Missing columns for line {}: {}".format(line_num, " ".join(fields)))
					if not args.ignore_errors:
						raise

				try:
					coords = dict([(name.lower(), type_cast(fields[index])) for name, type_cast, index in zip(
													coord_column_names, coord_column_types, coord_column_indices)])

					scores = dict([(p, score_value(fields[i])) for p, i in zip(predictors, score_indices)])
				except Exception as ex:
					logger.error("{} at line {}: {}".format(str(ex), line_num, " ".join(fields)))
					if not args.ignore_errors:
						raise

				try:
					for row in db.query_scores(fields=[], **coords):
						db.update_scores(row["id"], scores)
				except Exception as ex:
					logger.error("Error updating SNV at line {}: {}".format(line_num, str(ex)))
					logger.error("SNV: {}".format(", ".join(["{}={}".format(k, v) for k, v in coords.items()])))
					if not args.ignore_errors:
						raise

				progress.update()

		progress.log_totals()

		logger.info("Finalizing database ...")

		if args.update_predictors:
			logger.info("Updating predictors ...")
			db.update_predictors()

		logger.info("Committing ...")
		db.commit()

		logger.info("Finished successfully. Elapsed time: {}".format(progress.elapsed_time))

	except:
		return cmd.handle_error()
	finally:
		db.close()

	return 0

if __name__ == "__main__":
	exit(main())
