#!/usr/bin/env python

import argparse

from fannsdb.cmdhelper import DefaultCommandHelper

def main():
	parser = argparse.ArgumentParser(
		description="Create a functional scores database")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()
	
	parser.add_argument("predictors", metavar="PREDICTORS", nargs="*",
						help="Predictor identifiers")

	args, logger = cmd.parse_args("create")

	db = cmd.create_db()

	try:
		for predictor_id in args.predictors:
			logger.info("Adding predictor {} ...".format(predictor_id))
			db.add_predictor(predictor_id, FannsDb.SOURCE_PREDICTOR_TYPE)

		db.set_initialized()

		db.commit()
	except:
		return cmd.handle_error()
	finally:
		db.close()

	return 0

if __name__ == "__main__":
	exit(main())
