#!/usr/bin/env python

"""
Import ICDO terms into the database

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
"""

from wok.task import Task

from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.biomart import biomart_db_connect, map_from_file, \
							DEFAULT_INSERT_SIZE, DEFAULT_DB_ENGINE
from intogen.sql import BatchInsert

task = Task()

@task.main()
def main():
	task.check_conf(["entities", "repositories", "biomart.db",
		"biomart.files.icdo_topography", "biomart.files.icdo_morphology"])
	conf = task.conf

	insert_size = conf.get("biomart.insert_size", DEFAULT_INSERT_SIZE, dtype=int)

	log = task.logger()

	icdo_port = task.ports("icdo")

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])

	log.info("Loading topography codes from {} ...".format(conf["biomart.files.icdo_topography"]))
	icdo_repo, icdo_path = rs.from_url(conf["biomart.files.icdo_topography"])
	icdo_local_path = icdo_repo.get_local(icdo_path)
	icdo_topography = map_from_file(icdo_local_path)
	icdo_repo.close_local(icdo_path)
	icdo_repo.close()

	log.info("Loading morphology codes from {} ...".format(conf["biomart.files.icdo_morphology"]))
	icdo_repo, icdo_path = rs.from_url(conf["biomart.files.icdo_morphology"])
	icdo_local_path = icdo_repo.get_local(icdo_path)
	icdo_morphology = map_from_file(icdo_local_path)
	icdo_repo.close_local(icdo_path)
	icdo_repo.close()

	conn = biomart_db_connect(conf["biomart.db"], log)

	db_engine = conf.get("biomart.db.engine", DEFAULT_DB_ENGINE)

	cursor = conn.cursor()

	cursor.execute("""
		CREATE TABLE  ent_icdo (
		  id int(11) NOT NULL,
		  icdo_name varchar(512) NOT NULL DEFAULT '',
		  icdo_topography varchar(255) NOT NULL DEFAULT '',
		  icdo_morphology varchar(255) NOT NULL DEFAULT '',
		  icdo_topography_code varchar(24) NOT NULL DEFAULT '',
		  icdo_morphology_code varchar(24) NOT NULL DEFAULT '',
		  icdo_topography_name varchar(255) NOT NULL DEFAULT '',
		  icdo_morphology_name varchar(255) NOT NULL DEFAULT '',
		  PRIMARY KEY (id),
		  KEY icdo_name (icdo_name),
		  KEY icdo_tm (icdo_topography,icdo_morphology),
		  KEY icdo_m (icdo_morphology),
		  KEY icdo_tm_c (icdo_topography_code,icdo_morphology_code),
		  KEY icdo_m_c (icdo_morphology_code)
		) ENGINE={} DEFAULT CHARSET=latin1""".format(db_engine))

	ib = BatchInsert(cursor, "ent_icdo",
			["id", "icdo_name", "icdo_topography", "icdo_topography_code", "icdo_topography_name",
				"icdo_morphology", "icdo_morphology_code", "icdo_morphology_name"], insert_size)

	for i, tm in enumerate(icdo_port, 1):
		t_code = tm[0]
		if t_code == "":
			t_name = t_desc = "ANY topography"
		elif t_code not in icdo_topography:
			log.error("Unknown topography description for code {}".format(t_code))
			t_name = ""
			t_desc = "[{}]".format(t_code)
		else:
			t_name = icdo_topography[t_code]
			t_desc = "{} [{}]".format(t_name, t_code)

		m_code = tm[1]
		if m_code == "":
			m_name = m_desc = "ANY morphology"
		elif m_code not in icdo_morphology:
			log.error("Unknown morphology description for code {}".format(m_code))
			m_name = ""
			m_desc = "[{}]".format(m_code)
		else:
			m_name = icdo_morphology[m_code]
			m_desc = "{} [{}]".format(m_name, m_code)

		name = "; ".join((t_desc, m_desc))

		log.info("({}, {}) --> ({}, {})".format(t_code, m_code, t_desc, m_desc))

		ib.insert(i, name, t_desc, t_code, t_name, m_desc, m_code, m_name)

	log.debug("{} ICDO terms inserted".format(ib.count))

	ib.close()
	cursor.close()
	conn.close()
	em.close()
	es.close()
	rs.close()

task.start()