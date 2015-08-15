#!/usr/bin/env python

import os
import argparse

from collections import defaultdict

from bgcore import tsv

from fannsdb.cmdhelper import DefaultCommandHelper
from fannsdb.utils import RatedProgress

def main():
	parser = argparse.ArgumentParser(
		description="Filter for the longest transcript")

	cmd = DefaultCommandHelper(parser)

	parser.add_argument("len_path", metavar="PATH",
						help="The tsv containing the transcripts length")

	parser.add_argument("data_path", metavar="PATH",
						help="The data file")

	parser.add_argument("out_path", metavar="PATH",
						help="Output file. Use - for standard output.")

	parser.add_argument("-k", "--key", dest="key", metavar="KEY", default="PROTEIN,AA_POS,AA_REF,AA_ALT",
						help="List of columns that conforms the key. Default: PROTEIN,AA_POS,AA_REF,AA_ALT")

	args, logger = cmd.parse_args("filter-transcript")

	try:
		logger.info("Loading transcripts length ...")
		trslen = defaultdict(int)
		with tsv.open(args.len_path) as f:
			for name, length in tsv.rows(f):
				trslen[name] = length

		logger.info("Filtering {} ...".format(os.path.basename(args.data_path)))

		total_count = filter_count = 0

		progress = RatedProgress(logger, name="mutations")

		key_columns = args.key.split(",")
		with tsv.open(args.data_path, "r") as df, tsv.open(args.out_path, "w") as of:
			hdr_line = df.readline()
			of.write(hdr_line)
			_, hdr = tsv.header_from_line(hdr_line)
			key_indices = [hdr[name] for name in key_columns]
			trs_index = hdr["TRANSCRIPT"]

			last_key = None
			longest = (0, "")

			for line in df:
				total_count += 1

				fields = line.rstrip("\n").split("\t")
				key = tuple([fields[index] for index in key_indices])
				trs = fields[trs_index]

				tl = trslen[trs]

				if last_key != key:
					if last_key is not None:
						of.write(longest[1])
						filter_count += 1
					longest = (tl, line)
					last_key = key

				elif tl > longest[0]:
					longest = (tl, line)

				progress.update()

			filter_count += 1
			of.write(longest[1])

		progress.log_totals()

		logger.info("Finished. in={}, out={}, filtered={}, elapsed={}".format(
			total_count, filter_count, total_count - filter_count, progress.elapsed_time))
	except:
		cmd.handle_error()

	return 0

if __name__ == "__main__":
	exit(main())
