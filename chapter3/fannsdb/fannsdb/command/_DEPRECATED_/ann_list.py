#!/usr/bin/env python

import os
import argparse

from bgcore import tsv

from fannsdb.cmdhelper import DefaultCommandHelper

def main():
	parser = argparse.ArgumentParser(
		description="List annotations")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	args, logger = cmd.parse_args("ann-list")

	db = cmd.open_db()

	try:
		print "\t".join(["ID", "NAME", "TYPE", "PRIORITY"])
		for ann in db.maps():
			print "\t".join([str(ann[k]) for k in ["id", "name", "type", "priority"]])

	except:
		return cmd.handle_error()
	finally:
		db.close()

	return 0

if __name__ == "__main__":
	exit(main())
