#!/usr/bin/env python

"""
"""

from wok.config import Config
from wok.logger import get_logger, initialize

def main():
	conf = Config()

	initialize({"log":{"level":"debug"}})
	log = get_logger("mrna_preproc_counts")
	log.setLevel(logging.DEBUG)

	log.info("Querying log2r tumour units ...")

	es = EntityServer(conf["entities"])
	em = es.manager()

	

if __name__ == "__main__":
	main()
