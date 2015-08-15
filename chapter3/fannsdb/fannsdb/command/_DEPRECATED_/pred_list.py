#!/usr/bin/env python

import os
import argparse

from bgcore import tsv

from fannsdb.cmdhelper import DefaultCommandHelper

def main():
	parser = argparse.ArgumentParser(
		description="List predictors")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	parser.add_argument("--json", dest="to_json", action="store_true", default=False,
						help="Print the results in json format")

	args, log = cmd.parse_args("pred-list")

	db = cmd.open_db()

	try:
		if args.to_json:
			d = {}
			for pred in db.predictors():
				d[pred["id"]] = dict([(k,pred[k]) for k in ["type", "source", "min", "max", "count"]])
			import json
			print json.dumps(d, indent=True)
		else:
			print "\t".join(["ID", "TYPE", "SOURCE", "MIN", "MAX", "COUNT"])
			for pred in db.predictors():
				print "\t".join([str(pred[k]) for k in ["id", "type", "source", "min", "max", "count"]])

	except:
		return cmd.handle_error()
	finally:
		db.close()

	return 0

if __name__ == "__main__":
	exit(main())
