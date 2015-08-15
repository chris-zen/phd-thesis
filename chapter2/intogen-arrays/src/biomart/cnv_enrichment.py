#!/usr/bin/env python

"""
Export enrichment results to biomart database

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory

* Input:

- id: The (id-type, mrna.enrichment id) to export

* Entities:

- cnv.enrichment

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
	"gain_n", "gain_observed",
	"gain_expected_mean", "gain_expected_stdev",
	"gain_right_p_value", "gain_corrected_right_p_value",
	"loss_n", "loss_observed",
	"loss_expected_mean", "loss_expected_stdev",
	"loss_right_p_value", "loss_corrected_right_p_value"]

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
			continue
			
		cursor.execute("""
			CREATE TABLE IF NOT EXISTS exp_{0}_cna (
			  {0}_id int(11) NOT NULL,
			  icdo_id int(11) NOT NULL,
			  exp_id int(11) NOT NULL,
			  gain_total int(11) DEFAULT NULL,
			  gain_observed double DEFAULT NULL,
			  gain_expected double DEFAULT NULL,
			  gain_stdev double DEFAULT NULL,
			  gain_pvalue double DEFAULT NULL,
			  gain_cpvalue double DEFAULT NULL,
			  loss_total int(11) DEFAULT NULL,
			  loss_observed double DEFAULT NULL,
			  loss_expected double DEFAULT NULL,
			  loss_stdev double DEFAULT NULL,
			  loss_pvalue double DEFAULT NULL,
			  loss_cpvalue double DEFAULT NULL,
			  PRIMARY KEY ({0}_id,icdo_id,exp_id),
			  KEY icdo (icdo_id,exp_id),
			  KEY exp (exp_id),
			  CONSTRAINT exp_{0}_cna_{0}_id FOREIGN KEY ({0}_id) REFERENCES ent_{0} ({0}_id),
			  CONSTRAINT exp_{0}_cna_icdo_id FOREIGN KEY (icdo_id) REFERENCES ent_icdo (id),
			  CONSTRAINT exp_{0}_cna_exp_id FOREIGN KEY (exp_id) REFERENCES ent_experiment (id)
			) ENGINE={1} DEFAULT CHARSET=latin1""".format(name, db_engine))

		feat_ids[name] = map_from_select(cursor, "SELECT {0}_id, {0}_name FROM ent_{0}".format(name))

	icdo = map_from_select(cursor, "SELECT id, icdo_topography_code, icdo_morphology_code FROM ent_icdo")
	exp = map_from_select(cursor, "SELECT id, study_id, platf_id FROM ent_experiment")

	for id_type, eid in id_port:
		e = em.find(eid, types.CNV_ENRICHMENT)
		if e is None:
			log.error("{} not found: {}".format(types.CNV_ENRICHMENT, eid))
			continue

		if "results_file" not in e:
			log.error("{} [{}] without results file.".format(types.CNV_ENRICHMENT, eid))
			continue

		study_id = e["study_id"]
		platform_id = e["platform_id"]
		icdo_topography = e["icdo_topography"]
		icdo_morphology = e["icdo_morphology"]

		okey = (study_id, platform_id, icdo_topography, icdo_morphology, id_type)

		log.info("Exporting enrichment results ({}) [{}] ...".format(", ".join(okey), eid))

		table_infix = ID_TYPE_TO_TABLE_INFIX[id_type]

		icdo_key = (icdo_topography, icdo_morphology)
		if icdo_key not in icdo:
			log.error("ICDO ({}) not found in the database".format(", ".join(icdo_key)))
			continue
		icdo_id = icdo[icdo_key]

		exp_key = (study_id, platform_id)
		if exp_key not in exp:
			log.error("Experiment ({}) not found in the database".format(", ".join(exp_key)))
			continue
		exp_id = exp[exp_key]

		ib = BatchInsert(cursor, "exp_{}_cna".format(table_infix),
				["{}_id".format(table_infix), "icdo_id", "exp_id",
					"gain_total", "gain_observed", "gain_expected", "gain_stdev", "gain_pvalue", "gain_cpvalue",
					"loss_total", "loss_observed", "loss_expected", "loss_stdev", "loss_pvalue", "loss_cpvalue"],
				insert_size)

		results_repo, results_path = rs.from_url(e["results_file"])

		try:
			reader = results_repo.open_reader(results_path)
		except Exception as ex:
			log.exception(ex)
			ib.close()
			results_repo.close()
			continue
		
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

		skipped_ids = set()

		fids = feat_ids[table_infix]

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
			
			ib.insert(feat_id, icdo_id, exp_id, *data)

		if len(skipped_ids) > 0:
			log.warn("There were {} feature names not found:\n{}".format(len(skipped_ids), ",".join(skipped_ids)))

		log.debug("{} results inserted".format(ib.count))

		ib.close()
		reader.close()

	em.close()
	rs.close()

task.start()
