#!/usr/bin/env python

import argparse
import logging

from bgcore import tsv
from fannsdb.cmdhelper import DefaultCommandHelper
from fannsdb.mutations.parser import DnaAndProtMutationParser, PrematureEnd, UnexpectedToken, GENOMIC, PROTEIN
from fannsdb.utils import RatedProgress


def query_mutation(logger, db, mut, annotations, predictors):

	if mut.coord == GENOMIC:
		if logger.isEnabledFor(logging.DEBUG):
			logger.debug("  Querying {} {} {} {} {} {} {} ...".format(
				mut.chr, mut.start, mut.end or "*", mut.ref or "*", mut.alt, mut.strand or "*", mut.identifier or "*"))

		for row in db.query_scores(chr=mut.chr, start=mut.start,
										ref=mut.ref, alt=mut.alt, strand=mut.strand,
										predictors=predictors, maps=annotations):
			yield row

	elif mut.coord == PROTEIN:
		if logger.isEnabledFor(logging.DEBUG):
			logger.debug("  Querying {} {} {} {} {} ...".format(
				mut.protein, mut.start, mut.ref or "*", mut.alt, mut.identifier or "*"))

		for row in db.query_scores(protein=mut.protein, aa_pos=mut.start, aa_ref=mut.ref, aa_alt=mut.alt,
										predictors=predictors, maps=annotations):
			yield row

	else:
		logger.warn("Unknown coordinates system: {}".format(mut.line))

def main():
	parser = argparse.ArgumentParser(
		description="Fetch Condel scores")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	parser.add_argument("muts_path", metavar="SNVS_PATH",
						help="SNV's to check. Use - for standard input.")

	parser.add_argument("out_path", metavar="OUTPUT_PATH",
						help="The results path. Use - for standard output.")

	cmd.add_selected_predictors_args()

	cmd.add_selected_annotations_args()

	cmd.add_selected_columns_args()

	args, logger = cmd.parse_args("fetch")

	db = cmd.open_db()

	predictors = cmd.get_selected_predictors()

	annotations = cmd.get_selected_annotations()

	columns = cmd.get_selected_columns()

	logger.info("Reading {} ...".format(args.muts_path if args.muts_path != "-" else "from standard input"))

	try:
		progress = RatedProgress(logger, name="SNVs")

		with tsv.open(args.muts_path) as f:
			with tsv.open(args.out_path, "w") as wf:
				tsv.write_line(wf, "ID", *[c.upper() for c in columns] + [a.upper() for a in annotations] + predictors)

				hit = fail = 0

				mut = DnaAndProtMutationParser()
				for line_num, line in enumerate(f, start=1):
					line = line.rstrip(" \n\r")
					if len(line) == 0 or line.startswith("#"):
						continue

					try:
						mut.parse(line)
					except PrematureEnd:
						logger.error("Missing fields at line {}".format(line_num))
						fail += 1
						continue
					except UnexpectedToken as ex:
						logger.error("Unexpected field '{}' at line {}".format(ex.args[0], line_num))
						fail += 1
						continue

					exists = False
					for row in query_mutation(logger, db, mut, annotations, predictors):

						exists = True

						ann = row["annotations"]
						scores = row["scores"]

						tsv.write_line(wf, mut.identifier,
							   *[row[c] for c in columns]
							   + [ann[a] for a in annotations]
							   + [scores[p] for p in predictors])

						"""
						if logger.isEnabledFor(logging.DEBUG):
							logger.debug("    --> {} {} {} {} {} {} {} {} {} {}".format(
										row["chr"], row["start"], row["ref"], row["alt"], row["transcript"],
										row["protein"], row["aa_pos"], row["aa_ref"], row["aa_alt"],
										mut.identifier or "*"))
						"""

					progress.update()

					if exists:
						hit += 1
					else:
						fail += 1

		progress.log_totals()

		logger.info("Finished. total={}, hits={}, fails={}, elapsed={}".format(hit + fail, hit, fail, progress.elapsed_time))

	except:
		return cmd.handle_error()
	finally:
		db.close()

if __name__ == "__main__":
	exit(main())
