#!/bin/env python

import os
import argparse
import time
import gzip
import json
import random

from bgcore import tsv

from fannsdb.cmdhelper import DefaultCommandHelper
from fannsdb.utils import RatedProgress

def main():
	parser = argparse.ArgumentParser(
		description="Export Scores")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	parser.add_argument("dest_path", metavar="OUTPUT_PATH",
						help="The output file. Use - for standard output.")

	cmd.add_selected_predictors_args()

	cmd.add_selected_annotations_args()

	cmd.add_selected_columns_args()

	parser.add_argument("--json", dest="to_json", action="store_true", default=False,
						help="Export the results in json format")

	parser.add_argument("--sample", dest="sample", type=int, metavar="PCT",
						help="Export a random sample of PCT %%")

	parser.add_argument("--start", dest="start", type=int, metavar="N",
						help="Start to export from the SNV number N")

	parser.add_argument("--limit", dest="limit", type=int, metavar="N",
						help="Limit the number of SNVs to export to N")

	args, logger = cmd.parse_args("export")

	db = cmd.open_db()

	predictors = cmd.get_selected_predictors()

	annotations = cmd.get_selected_annotations()

	columns = cmd.get_selected_columns()

	logger.info("Exporting ...")

	random.seed(time.time())

	total_count = 0
	total_start_time = time.time()

	try:
		progress = RatedProgress(logger, name="SNVs")

		to_json = args.to_json
		sample = args.sample
		start = args.start or 0
		limit = args.limit

		doc = None
		last_pos = None
		rows_count = 0
		snvs_count = 0
		with tsv.open(args.dest_path, "w") as f:

			if not to_json:
				tsv.write_line(f, *[c.upper() for c in columns] + [a.upper() for a in annotations] + predictors)

			for row in db.query_scores(predictors=predictors, maps=annotations):

				if not to_json:
					if start > 0:
						start -= 1
						continue

					if sample is not None and random.randint(1, 100) > sample:
						continue

				pos = (row["chr"], row["strand"], row["start"], row["ref"], row["alt"])
				if last_pos != pos:
					if to_json:
						if start > 0:
							start -= 1
							continue

						if limit is not None and snvs_count >= limit:
							if doc is not None:
								json.dump(doc, f)
								f.write("\n")
							break

					snvs_count += 1

				rows_count += 1

				ann = row["annotations"]
				scores = row["scores"]

				if to_json:
					tdoc = dict([(k,row[k]) for k in ["transcript", "protein", "aa_pos", "aa_ref", "aa_alt"]] +
										[(k,scores[k]) for k in predictors])

					if pos != last_pos:
						if doc is not None:
							if sample is None or random.randint(1, 100) <= sample:
								json.dump(doc, f)
								f.write("\n")
							else:
								snvs_count -= 1

						doc = dict([(k, row[k]) for k in ["chr", "strand", "start", "ref", "alt"]] +
										[("transcripts", [tdoc])])
					else:
						doc["transcripts"] += [tdoc]

				else:
					tsv.write_line(f,
							   *[row[c] for c in columns]
							   + [ann[a] for a in annotations]
							   + [scores[p] for p in predictors])

				progress.update()

				last_pos = pos

				if not to_json and limit is not None and rows_count >= limit:
					break

		progress.log_totals()

		logger.info("Finished. Total rows = {}, SNVs = {}, elapsed_time = {}".format(rows_count, snvs_count, progress.elapsed_time))
	except:
		return cmd.handle_error()
	finally:
		db.close()

	return 0

if __name__ == "__main__":
	exit(main())