#!/usr/bin/env python

"""
Export combination results to biomart database

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory

* Input:

- id: The (id-type, mrna.combination id) to export

* Entities:

- mrna.combination

"""

from wok.task import Task

from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.data.entity import types
from intogen.biomart import biomart_db_connect, map_from_select, \
							DEFAULT_INSERT_SIZE, DEFAULT_DB_ENGINE, \
							ID_TYPE_TO_TABLE_INFIX
from intogen.sql import BatchInsert

# Initialization

task = Task()

__COLUMN_NAMES = [
	"upreg_n", "upreg_z_score", "upreg_p_value",
	"downreg_n", "downreg_z_score", "downreg_p_value"]

@task.main()
def main():
	task.check_conf(["entities", "repositories", "biomart.db"])
	conf = task.conf

	insert_size = conf.get("biomart.insert_size", DEFAULT_INSERT_SIZE, dtype=int)

	db_engine = conf.get("biomart.db.engine", DEFAULT_DB_ENGINE)
	
	log = task.logger()

	id_port = task.ports("id")

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])

	conn = biomart_db_connect(conf["biomart.db"], log)

	cursor = conn.cursor()

	table_infixs = set(ID_TYPE_TO_TABLE_INFIX.values())

	feat_ids = {}

	for name in table_infixs:
		if name == "gene":
			ref_id_prefix = ""
		else:
			ref_id_prefix = name + "_"

		cursor.execute("""
			CREATE TABLE IF NOT EXISTS cmb_{0}_trs (
			  {0}_id int(11) NOT NULL,
			  icdo_id int(11) NOT NULL,
			  upreg_n int(11) DEFAULT NULL,
			  upreg_zscore double DEFAULT NULL,
			  upreg_pvalue double DEFAULT NULL,
			  downreg_n int(11) DEFAULT NULL,
			  downreg_zscore double DEFAULT NULL,
			  downreg_pvalue double DEFAULT NULL,
			  PRIMARY KEY ({0}_id,icdo_id),
			  KEY icdo (icdo_id),
			  CONSTRAINT cmb_{0}_trs_{0}_id FOREIGN KEY ({0}_id) REFERENCES ent_{0} ({1}id),
			  CONSTRAINT cmb_{0}_trs_icdo_id FOREIGN KEY (icdo_id) REFERENCES ent_icdo (id)
			) ENGINE={2} DEFAULT CHARSET=latin1""".format(name, ref_id_prefix, db_engine))

		feat_ids[name] = map_from_select(cursor, "SELECT {1}id, {0}_name FROM ent_{0}".format(name, ref_id_prefix))

	icdo = map_from_select(cursor, "SELECT id, icdo_topography_code, icdo_morphology_code FROM ent_icdo")

	for id_type, eid in id_port:
		e = em.find(eid, types.MRNA_COMBINATION)
		if e is None:
			log.error("{} not found: {}".format(types.MRNA_COMBINATION, eid))
			continue

		if "results_file" not in e:
			log.error("{} [{}] without results file.".format(types.MRNA_COMBINATION, eid))
			continue

		icdo_topography = e["icdo_topography"]
		icdo_morphology = e["icdo_morphology"]

		key = (icdo_topography, icdo_morphology, id_type)

		log.info("Exporting combination results ({}) [{}] ...".format(", ".join(key), eid))

		table_infix = ID_TYPE_TO_TABLE_INFIX[id_type]

		icdo_key = (icdo_topography, icdo_morphology)
		if icdo_key not in icdo:
			log.error("ICDO ({}) not found in the database".format(", ".join(icdo_key)))
			continue
		icdo_id = icdo[icdo_key]

		ib = BatchInsert(cursor, "cmb_{}_trs".format(table_infix),
				["{}_id".format(table_infix), "icdo_id",
					"upreg_n", "upreg_zscore", "upreg_pvalue",
					"downreg_n", "downreg_zscore", "downreg_pvalue"], insert_size)

		results_repo, results_path = rs.from_url(e["results_file"])

		try:
			reader = results_repo.open_reader(results_path)
		except Exception as ex:
			log.exception(ex)
			ib.close()
			results_repo.close()
			continue

		skipped_ids = set()

		fids = feat_ids[table_infix]

		# read header
		hdr_map = {}
		hdr = reader.readline().rstrip().split("\t")
		for i, name in enumerate(hdr):
			hdr_map[name] = i

		try:
			col_indices = [hdr_map[x] for x in __COLUMN_NAMES]
		except KeyError as e:
			log.warn("Column {} not found in results files, most probably because it is empty".format(e.args[0]))
			reader.close()
			ib.close()
			results_repo.close()
			continue

		# read data
		for line in reader:
			line = line.rstrip()
			data = line.split("\t")
			feat_name = data[0]
			data = [data[i] for i in col_indices]
			if feat_name not in fids:
				skipped_ids.add(feat_name)
				continue

			feat_id = fids[feat_name]
			
			ib.insert(feat_id, icdo_id, *data)

		if len(skipped_ids) > 0:
			log.warn("There were {} feature names not found:\n{}".format(len(skipped_ids), ",".join(skipped_ids)))

		log.debug("{} results inserted".format(ib.count))

		ib.close()
		reader.close()

	em.close()
	es.close()
	rs.close()

task.start()
