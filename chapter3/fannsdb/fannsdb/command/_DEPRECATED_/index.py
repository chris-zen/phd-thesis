#!/bin/env python

import os
import re
import argparse

from datetime import datetime

from fannsdb.cmdhelper import DefaultCommandHelper

def main():
	parser = argparse.ArgumentParser(
		description="Manipulate database indices")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	parser.add_argument("ops", metavar="OPERATIONS", nargs="+", choices=["drop", "create"],
						help="The operations to perform on the indices.")

	args, logger = cmd.parse_args("index")

	db = cmd.open_db()

	try:
		start_time = datetime.now()

		for op in args.ops:
			if op == "drop":
				logger.info("Dropping indices ...")
				db.drop_indices()
			elif op == "create":
				logger.info("Creating indices ...")
				db.create_indices()

		elapsed_time = datetime.now() - start_time
		logger.info("Done. Elapsed time: {}".format(elapsed_time))
	except:
		return cmd.handle_error()
	finally:
		db.close()

	return 0

if __name__ == "__main__":
	exit(main())
