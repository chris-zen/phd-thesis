#!/bin/env python

import os
import re
import argparse

from datetime import datetime

from fannsdb.cmdhelper import DefaultCommandHelper

def main():
	parser = argparse.ArgumentParser(
		description="Update predictors min, max and count")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	cmd.add_selected_predictors_args()

	args, logger = cmd.parse_args("pred-update")

	db = cmd.open_db()

	try:
		predictors = cmd.get_selected_predictors(default_all=True)

		logger.info("Updating predictors ...")

		start_time = datetime.now()

		db.update_predictors(predictors)

		db.commit()

		logger.info("Finished. elapsed={}".format(datetime.now() - start_time))
	except:
		return cmd.handle_error()
	finally:
		db.close()

	return 0

if __name__ == "__main__":
	exit(main())
