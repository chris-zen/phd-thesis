#!/usr/bin/env python

"""
Import experiments into the database

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
"""

from wok.task import Task
from wok.element import DataElementList

from intogen.data.entity import types
from intogen.data.entity.server import EntityServer
from intogen.biomart import biomart_db_connect, DEFAULT_INSERT_SIZE, DEFAULT_DB_ENGINE
from intogen.sql import BatchInsert
from pubmed import Pubmed

task = Task()

@task.main()
def main():
	task.check_conf(["entities", "repositories", "biomart.db"])
	conf = task.conf

	insert_size = conf.get("biomart.insert_size", DEFAULT_INSERT_SIZE, dtype=int)

	if "biomart.study_source" in conf:
		study_source_map = conf["biomart.study_source"]
	else:
		study_source_map = conf.create_element()

	log = task.logger()

	exp_port = task.ports("experiment")
	
	es = EntityServer(conf["entities"])
	em = es.manager()

	conn = biomart_db_connect(conf["biomart.db"], log)

	db_engine = conf.get("biomart.db.engine", DEFAULT_DB_ENGINE)

	cursor = conn.cursor()

	cursor.execute("""
		CREATE TABLE ent_experiment (
		  id int(11) NOT NULL,
		  exp_name varchar(64) NOT NULL,
		  study_id varchar(32) NOT NULL,
		  study_source varchar(32) DEFAULT NULL,
		  study_source_url varchar(512) DEFAULT NULL,
		  study_link varchar(512) DEFAULT NULL,
		  pub_pubmed varchar(32) DEFAULT NULL,
		  pub_title varchar(300) DEFAULT NULL,
		  pub_authors varchar(300) DEFAULT NULL,
		  pub_year varchar(16) DEFAULT NULL,
		  pub_journal varchar(200) DEFAULT NULL,
		  platf_id varchar(32) NOT NULL,
		  platf_title varchar(250) DEFAULT NULL,
		  platf_technology varchar(96) DEFAULT NULL,
		  PRIMARY KEY (id),
		  KEY exp_name (exp_name),
		  KEY pub_pubmed (pub_pubmed),
		  KEY pub_title (pub_title),
		  KEY pub_authors (pub_authors),
		  KEY pub_year (pub_year),
		  KEY pub_journal (pub_journal),
		  KEY platf_title (platf_title),
		  KEY platf_technology (platf_technology)
		) ENGINE={} CHARACTER SET utf8 COLLATE utf8_general_ci""".format(db_engine))

	ib = BatchInsert(cursor, "ent_experiment",
			["id", "exp_name", "study_id", "study_source", "study_source_url", "study_link",
				"pub_title", "pub_authors", "pub_year", "pub_pubmed", "pub_journal",
				"platf_id", "platf_title", "platf_technology"], insert_size)

	pubmed = Pubmed()

	for i, exp in enumerate(exp_port, 1):
		study_id = exp[0]
		platform_id = exp[1]

		study = em.find(study_id, types.SOURCE_STUDY)
		if study is None:
			log.error("{} not found: {}".format(types.SOURCE_STUDY, study_id))
			continue

		platf = em.find(platform_id, types.SOURCE_PLATFORM)
		if platf is None:
			log.error("{} not found: {}".format(types.SOURCE_PLATFORM, platform_id))
			continue

		log.info("Experiment for study {} and platform {} ...".format(study_id, platform_id))

		pub = {}
		for k in ["title", "short_authors", "date", "journal"]:
			pub[k] = None

		if "pubmed" in study:
			pmid = study["pubmed"]
			if isinstance(pmid, (DataElementList, list)):
				pmid = pmid[0]
				log.warn("Study {} with many pubmed_id's, only the first {} will be considered".format(study_id, pmid))

			log.debug("Retrieving information for pubmed_id '{}' ...".format(pmid))
			try:
				pub = pubmed.find(pmid)
				if len(pub) == 0:
					log.error("No publication information found for pubmed_id '{}' in experiment ({}, {})".format(pmid, study_id, platform_id))
				else:
					pub = pub[0]
			except Exception as ex:
				log.error("Error retrieving pubmed information for experiment ({}, {}) with pubmed_id '{}'".format(study_id, platform_id, pmid))
				log.exception(ex)
		else:
			pmid = None
			log.warn("Study {} has no 'pubmed_id' annotation".format(study_id))

			if "title" not in study:
				log.error("Study {} doesn't have annotation for 'pubmed_id' nor 'title'".format(study_id))
			elif "SO/contact_details[0]/contact_name" not in study \
					and "SO/contact_details/contact_name" not in study:
				log.error("Study {} doesn't have annotation for 'pubmed_id' nor 'SO.contact_details[0].contact_name'".format(study_id))
			else:
				try:
					pub["title"] = study["title"]

					if "SO/contact_details[0]/contact_name" in study:
						pub["short_authors"] = study["SO/contact_details[0]/contact_name"]
					else:
						pub["short_authors"] = study["SO/contact_details/contact_name"]

					if "SO/submission/pub_date" in study:
						pub["date"] = study["SO/submission/pub_date"]
					else:
						pub["date"] = ""
				except Exception as ex:
					log.debug(study)
					log.execption(ex)

		for k, v in pub.items():
			if v is not None and isinstance(v, basestring):
				pub[k] = v.replace("'", r"\'")

		exp_name = "{}; {}".format(study_id, platform_id)

		study_source = None
		study_source_url = None
		study_link = None

		parts = study_id.split("-")
		if len(parts) >= 2 and parts[0] in study_source_map:
			ss = study_source_map[parts[0]]
			study_source = ss.get("name")
			study_source_url = ss.get("home_url")
			try:
				study_link = ss.get("link", "").format(parts[1])
			except:
				pass

		ib.insert(i, exp_name, study_id, study_source, study_source_url, study_link,
			pub["title"], pub["short_authors"], pub["date"], pmid, pub["journal"],
			platform_id, platf["SO/platform_title"], "")

	log.debug("{} experiments inserted".format(ib.count))

	ib.close()
	cursor.close()
	conn.close()
	em.close()
	es.close()

task.start()
