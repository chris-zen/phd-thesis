#!/bin/env python

import os
import argparse
import logging
import time
import gzip

from bgcore import tsv

from fannsdb.cmdhelper import DefaultCommandHelper
from fannsdb.utils import RatedProgress

def main():
	parser = argparse.ArgumentParser(
		description="Export SNV's")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	parser.add_argument("dest_path", metavar="DEST",
						help="The destination file. Use - for standard output.")

	args, log = cmd.parse_args("export-snvs")

	db = cmd.open_db()

	logger.info("Exporting SNV's ...")

	total_count = 0
	total_start_time = time.time()

	try:
		progress = RatedProgress(logger, name="SNVs")
		rows_count = 0
		with tsv.open(args.dest_path, "w") as f:
			for snv in db.snvs():
				rows_count += 1

				tsv.write_line(f, snv["chr"], snv["start"], snv["start"], snv["strand"], "{}>{}".format(snv["ref"], snv["alt"]), "S")

				progress.update()

		log.info("Finished. Total rows = {}, elapsed_time = {}".format(rows_count, progress.elapsed_time))
	except:
		return cmd.handle_error()
	finally:
		db.close()

	return 0

if __name__ == "__main__":
	exit(main())