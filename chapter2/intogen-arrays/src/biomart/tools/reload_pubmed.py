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

	pubmed = Pubmed()

	log.info("Connecting ...")

	conn = biomart_db_connect(conf["biomart.db"], log)

	cursor = conn.cursor()

	update_cursor = conn.cursor()

	log.info("Querying experiments ...")

	cursor.execute("""
		select id, pub_pubmed, study_id, platf_id
		from ent_experiment where pub_pubmed is not NULL""")

	SPACES = re.compile("\s+")

	row = cursor.fetchone()
	while row is not None:
		id, pmid, study_id, platf_id = row

		log.info(">>> PMID: {}, STUDY: {}, PLATFORM: {}".format(pmid, study_id, platf_id))

		pub = pubmed.find(pmid)
		if pub is None:
			log.error("PMID not found: {}".format(pmid))
			continue

		pub = pub[0]
		for k, v in pub.items():
			if v is not None and isinstance(v, basestring):
				pub[k] = v.replace("'", r"\'")

		sql = u"""
			update ent_experiment
			set pub_title='{}', pub_authors='{}', pub_year='{}', pub_journal='{}'
			where id={}""".format(
				pub["title"], pub["short_authors"],
				pub["date"], pub["journal"], id)

		log.debug(SPACES.sub(" ", sql.strip()))

		update_cursor.execute(sql)

		row = cursor.fetchone()
	
	cursor.close()
	update_cursor.close()
	conn.close()
	
if __name__ == "__main__":
	main()
