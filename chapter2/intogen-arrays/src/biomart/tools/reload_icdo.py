#!/usr/bin/env python

"""
"""

import re
import logging

from wok.config import Config
from intogen.biomart import biomart_db_connect

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

	cursor.execute("""select id, icdo_topography, icdo_topography_code,
	icdo_morphology, icdo_morphology_code from ent_icdo""")

	SPACES = re.compile("\s+")
	TOPOGRAPHY = re.compile(r"^\[C\d\d(\.\d)?\] (.+)")
	TOPOGRAPHY2 = re.compile(r"(.+) \[C\d\d(\.\d)?\]$")
	MORPHOLOGY = re.compile(r"^\[\d\d\d\d\/\d\] (.+)")

	row = cursor.fetchone()
	while row is not None:
		id, icdo_topography, icdo_topography_code, icdo_morphology, icdo_morphology_code = row

		row = cursor.fetchone()

		log.info(">>> ID: {}, T: {}, M: {}".format(id, icdo_topography, icdo_morphology))

#		if icdo_morphology != "ANY morphology":
#			continue

#		m = TOPOGRAPHY.match(icdo_topography)
#		if m is None:
#			log.error("Wrong topography: {}".format(icdo_topography))
#			continue
#
#		icdo_topography = m.group(2)

#		m = MORPHOLOGY.match(icdo_morphology)
#		if m is None:
#			log.error("Wrong morphology: {}".format(icdo_morphology))
#			continue
#
#		icdo_morphology = m.group(1)

		#icdo_name = "{} [{}]; {} [{}]".format(icdo_topography, icdo_topography_code, icdo_morphology, icdo_morphology_code)

#		icdo_name = "{} [{}]; {}".format(icdo_topography, icdo_topography_code, icdo_morphology)

#		sql = u"""
#			update ent_icdo
#			set icdo_name='{}',
#			icdo_topography='{}',
#			icdo_morphology='{}'
#			where id={}""".format(icdo_name, icdo_topography, icdo_morphology, id)

#		icdo_topography_name = icdo_topography
#		icdo_topography = "{} [{}]".format(icdo_topography, icdo_topography_code)
#
#		icdo_morphology_name = icdo_morphology
#		if icdo_morphology != "ANY morphology":
#			icdo_morphology = "{} [{}]".format(icdo_morphology, icdo_morphology_code)

#		sql = u"""
#			update ent_icdo
#			set icdo_topography='{}', icdo_morphology_name='{}',
#			icdo_morphology='{}', icdo_morphology_name='{}'
#			where id={}""".format(icdo_topography, icdo_topography_name, icdo_morphology, icdo_morphology_name, id)

		m = TOPOGRAPHY2.match(icdo_topography)
		if m is None:
			log.error("Wrong topography: {}".format(icdo_topography))
			continue

		icdo_topography_name = m.group(1)

		sql = u"""
			update ent_icdo
			set icdo_topography_name='{}'
			where id={}""".format(icdo_topography_name, id)

		log.debug(SPACES.sub(" ", sql.strip()))

		update_cursor.execute(sql)

	cursor.close()
	update_cursor.close()
	conn.close()

if __name__ == "__main__":
	main()
