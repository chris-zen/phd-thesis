#!/usr/bin/env python

"""
Export oncodrive results to biomart database

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory

* Input:

- id: The mrna.oncodrive_gene ids to export

* Entities:

- mrna.oncodrive_genes

"""

from wok.task import Task

from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.data.entity import types
from intogen.biomart import biomart_db_connect, map_from_select, \
							DEFAULT_INSERT_SIZE, DEFAULT_DB_ENGINE
from intogen.sql import BatchInsert

# Initialization

task = Task()

__COLUMN_NAMES = [
	"upreg_n", "upreg_observed",
	"upreg_expected_mean", "upreg_expected_stdev",
	"upreg_right_p_value", "upreg_corrected_right_p_value",
	"downreg_n", "downreg_observed",
	"downreg_expected_mean", "downreg_expected_stdev",
	"downreg_right_p_value", "downreg_corrected_right_p_value"]

@task.main()
def main():
	task.check_conf(["entities", "repositories", "biomart.db"])
	conf = task.conf

	insert_size = conf.get("biomart.insert_size", DEFAULT_INSERT_SIZE, dtype=int)

	db_engine = conf.get("biomart.db.engine", DEFAULT_DB_ENGINE)

	log = task.logger()

	oncodrive_port = task.ports("id")

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])

	conn = biomart_db_connect(conf["biomart.db"], log)

	cursor = conn.cursor()

	gene = map_from_select(cursor, "SELECT id, gene_name FROM ent_gene")
	icdo = map_from_select(cursor, "SELECT id, icdo_topography_code, icdo_morphology_code FROM ent_icdo")
	exp = map_from_select(cursor, "SELECT id, study_id, platf_id FROM ent_experiment")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS exp_gene_trs (
		  gene_id int(11) NOT NULL,
		  icdo_id int(11) NOT NULL,
		  exp_id int(11) NOT NULL,
		  upreg_total int(11) DEFAULT NULL,
		  upreg_observed double DEFAULT NULL,
		  upreg_expected double DEFAULT NULL,
		  upreg_stdev double DEFAULT NULL,
		  upreg_pvalue double DEFAULT NULL,
		  upreg_cpvalue double DEFAULT NULL,
		  downreg_total int(11) DEFAULT NULL,
		  downreg_observed double DEFAULT NULL,
		  downreg_expected double DEFAULT NULL,
		  downreg_stdev double DEFAULT NULL,
		  downreg_pvalue double DEFAULT NULL,
		  downreg_cpvalue double DEFAULT NULL,
		  PRIMARY KEY (gene_id,icdo_id,exp_id),
		  KEY icdo (icdo_id,exp_id),
		  KEY exp (exp_id),
		  CONSTRAINT exp_gene_trs_gene_id FOREIGN KEY (gene_id) REFERENCES ent_gene (id),
		  CONSTRAINT exp_gene_trs_icdo_id FOREIGN KEY (icdo_id) REFERENCES ent_icdo (id),
		  CONSTRAINT exp_gene_trs_exp_id FOREIGN KEY (exp_id) REFERENCES ent_experiment (id)
		) ENGINE={} DEFAULT CHARSET=latin1""".format(db_engine))

	cursor.execute("LOCK TABLES exp_gene_trs WRITE")

	lock_count = 0
	
	for eid in oncodrive_port:
		e = em.find(eid, types.MRNA_ONCODRIVE_GENES)
		if e is None:
			log.error("{} not found: {}".format(types.MRNA_ONCODRIVE_GENES, eid))
			continue

		if "results_file" not in e:
			log.error("{} [{}] without results file.".format(types.MRNA_ONCODRIVE_GENES, eid))
			continue

		study_id = e["study_id"]
		platform_id = e["platform_id"]
		icdo_topography = e["icdo_topography"]
		icdo_morphology = e["icdo_morphology"]

		okey = (study_id, platform_id, icdo_topography, icdo_morphology)

		log.info("Exporting oncodrive results ({}) [{}] ...".format(", ".join(okey), eid))

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

		ib = BatchInsert(cursor, "exp_gene_trs",
				["gene_id", "icdo_id", "exp_id",
					"upreg_total", "upreg_observed", "upreg_expected", "upreg_stdev", "upreg_pvalue", "upreg_cpvalue",
					"downreg_total", "downreg_observed", "downreg_expected", "downreg_stdev", "downreg_pvalue", "downreg_cpvalue"],
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
			lock_count += ib.count
			ib.close()
			results_repo.close()
			continue

		skipped_genes = set()

		# read data
		for line in reader:
			line = line.rstrip()
			data = line.split("\t")
			gene_name = data[0]
			data = [data[i] for i in col_indices]
			if gene_name not in gene:
				skipped_genes.add(gene_name)
				continue

			gene_id = gene[gene_name]
			
			ib.insert(gene_id, icdo_id, exp_id, *data)

		if len(skipped_genes) > 0:
			log.warn("There were {} gene names not found:\n{}".format(len(skipped_genes), ",".join(skipped_genes)))

		log.debug("{} gene results inserted".format(ib.count))

		lock_count += ib.count
		
		ib.close()
		reader.close()

		if lock_count >= 1000000:
			cursor.execute("UNLOCK TABLES")
			cursor.execute("OPTIMIZE NO_WRITE_TO_BINLOG TABLE exp_gene_trs")
			cursor.execute("LOCK TABLES exp_gene_trs WRITE")
			lock_count = 0

	cursor.execute("UNLOCK TABLES")
	cursor.execute("OPTIMIZE NO_WRITE_TO_BINLOG TABLE exp_gene_trs")
	cursor.close()

	em.close()
	es.close()
	rs.close()

task.start()
