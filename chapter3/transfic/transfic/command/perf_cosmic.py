#!/usr/bin/env python

import os
import argparse
import tarfile
import re
import json

from collections import defaultdict

from bgcore import tsv
from bgcore.re import ReContext

from fannsdb.cmdhelper import DefaultCommandHelper
from fannsdb.utils import RatedProgress
from fannsdb.cosmic import extract_snvs, create_datasets

def main():
	parser = argparse.ArgumentParser(
		description="Generate datasets needed to evaluate performance from Cosmic mutations")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	parser.add_argument("data_path", metavar="PATH",
						help="The CosmicMutantExport tsv file")

	parser.add_argument("cgc_path", metavar="PATH",
						help="The list of CGC genes")

	parser.add_argument("tdrivers_path", metavar="PATH",
						help="The list of TD drivers")
	
	parser.add_argument("pdrivers_path", metavar="PATH",
						help="The list of PD drivers")

	parser.add_argument("-o", dest="prefix", metavar="PREFIX",
						help="Output prefix.")

	args, logger = cmd.parse_args("perf-cosmic")

	fanns_db = cmd.open_db()

	try:
		snvs = extract_snvs(fanns_db, args.data_path, logger=logger)

		create_datasets(snvs, args.cgc_path, args.tdrivers_path, args.pdrivers_path, args.prefix)
	except:
		cmd.handle_error()

	return 0

if __name__ == "__main__":
	exit(main())
