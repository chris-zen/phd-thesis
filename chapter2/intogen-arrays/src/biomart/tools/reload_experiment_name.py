#!/usr/bin/env python

"""
"""

import re
import logging

from wok.config import Config
from intogen.biomart import biomart_db_connect
from pubmed import Pubmed

def main():
	conf = Config()

	logging.basicConfig(format = "%(asctime)s %(name)s %(levelname) -5s : %(message)s")
	log = logging.getLogger("reload_pubmed")
	log.setLevel(logging.DEBUG)

	log.info("Connecting ...")

	conn = biomart_db_connect(conf["biomart.db"], log)

	cursor = conn.cursor()

	update_cursor = conn.cursor()

	log.info("Querying experiments ...")

	cursor.execute("""select id, pub_pubmed, study_id, platf_id from ent_experiment""")

	SPACES = re.compile("\s+")

	row = cursor.fetchone()
	while row is not None:
		id, pmid, study_id, platf_id = row

		log.info(">>> PMID: {}, STUDY: {}, PLATFORM: {}".format(pmid, study_id, platf_id))

		exp_name = "; ".join((study_id, platf_id))

		sql = u"""
			update ent_experiment
			set exp_name='{}' where id={}""".format(exp_name, id)

		log.debug(SPACES.sub(" ", sql.strip()))

		update_cursor.execute(sql)

		row = cursor.fetchone()

	cursor.close()
	update_cursor.close()
	conn.close()

if __name__ == "__main__":
	main()
