#!/usr/bin/env python

import os
import argparse

from bgcore import tsv

from fannsdb.cmdhelper import DefaultCommandHelper

def main():
	parser = argparse.ArgumentParser(
		description="Remove annotations")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	parser.add_argument("id", metavar="ID", nargs="+",
						help="Annotation identifier.")

	args, logger = cmd.parse_args("ann-rm")

	db = cmd.open_db()

	try:
		if "*" in args.id:
			logger.info("Removing all the annotations ...")
			for ann in db.maps():
				logger.info("  {} {} ...".format(ann["id"], ann["name"]))
				db.remove_map(ann["id"])
		else:
			for ann_id in args.id:
				logger.info("Removing annotation {} ...".format(ann_id))
				db.remove_map(ann_id)

		db.commit()
	except:
		return cmd.handle_error()
	finally:
		db.close()

	return 0

if __name__ == "__main__":
	exit(main())
