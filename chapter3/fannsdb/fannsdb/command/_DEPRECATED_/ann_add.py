#!/usr/bin/env python

import os
import argparse

from bgcore import tsv

from fannsdb.cmdhelper import DefaultCommandHelper

def main():
	parser = argparse.ArgumentParser(
		description="Add annotations")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	parser.add_argument("id", metavar="ID",
						help="Annotation identifier.")

	parser.add_argument("name", metavar="NAME",
						help="Annotation name.")

	parser.add_argument("type", metavar="TYPE", choices=["transcript", "protein"],
						help="Annotation type: transcript, protein")

	parser.add_argument("path", metavar="PATH", 
						help="Annotation items")

	parser.add_argument("--priority", dest="priority", default=0,
						help="Priority for translating input annotations. 0 means not considered for translation. Default 0.")

	parser.add_argument("--header", dest="header", action="store_true", default=False,
						help="Specify that the annotation items file have a header.")

	args, logger = cmd.parse_args("ann-add")

	db = cmd.open_db()

	try:
		logger.info("Creating annotation {} ...".format(args.name))

		db.add_map(args.id, args.name, args.type, args.priority)

		logger.info("Loading items ...")

		with tsv.open(args.path) as f:
			for source, value in tsv.lines(f, (str, str), header=args.header):
				if len(source) > 0 and len(value) > 0:
					db.add_map_item(args.id, source, value)

		db.commit()
	except:
		return cmd.handle_error()
	finally:
		db.close()

	return 0

if __name__ == "__main__":
	exit(main())
