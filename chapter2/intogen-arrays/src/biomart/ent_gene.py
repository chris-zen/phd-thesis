#!/usr/bin/env python

"""
Get gene data from ensembl and import into biomart database

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory

"""

from wok.task import Task
from intogen.biomart import biomart_db_connect, DEFAULT_INSERT_SIZE


# Initialization

task = Task()

@task.main()
def main():
	conf = task.conf

	insert_size = conf.get("biomart.insert_size", DEFAULT_INSERT_SIZE, dtype=int)

	log = task.logger()

	rs = RepositoryServer(conf["repositories"])

	conn = biomart_db_connect(conf["biomart.db"], log)

	cursor = conn.cursor()

	log.info("Creating table ...")

	cursor.execute("DROP TABLE IF EXISTS ent_gene")
	cursor.execute("""
		CREATE TABLE `ent_gene` (
		  `id` int(11) NOT NULL,
		  `gene_name` varchar(32) NOT NULL,
		  `gene_sym` varchar(48) DEFAULT NULL,
		  `gene_desc` varchar(1020) DEFAULT '',
		  `gene_chr` varchar(16) DEFAULT NULL,
		  `gene_band` varchar(20) DEFAULT NULL,
		  `gene_strand` int(2) DEFAULT NULL,
		  `gene_pos_start` int(11) DEFAULT NULL,
		  `gene_pos_end` int(11) DEFAULT NULL,
		  `gene_biotype` varchar(22) DEFAULT NULL,
		  `gene_status` varchar(12) DEFAULT NULL,
		  `gene_source` varchar(14) DEFAULT NULL,
		  `gene_transcript_count` int(3) DEFAULT NULL,
		  `gene_gc_content` double DEFAULT NULL,
		  PRIMARY KEY (`id`),
		  KEY `gene_name` (`gene_name`),
		  KEY `gene_sym` (`gene_sym`),
		  KEY `gene_chr` (`gene_chr`),
		  KEY `gene_band` (`gene_band`),
		  KEY `gene_strand` (`gene_strand`),
		  KEY `gene_pos_start` (`gene_pos_start`),
		  KEY `gene_pos_end` (`gene_pos_end`),
		  KEY `gene_biotype` (`gene_biotype`)
		) ENGINE=InnoDB DEFAULT CHARSET=latin1""")
	
	insert_sql = """INSERT INTO `ent_gene` (
		`id`, `gene_name`, `gene_sym`, `gene_desc`, `gene_chr`, `gene_band`, `gene_strand`,
		`gene_pos_start`, `gene_pos_end`, `gene_biotype`, `gene_status`, `gene_source`,
		`gene_transcript_count`, `gene_gc_content`) VALUES"""
	
	ib = BatchInsert(cursor, insert_sql, insert_size)

	repo, path = rs.from_url(conf["biomart.files.gene"])

	local_path = repo.get_local(path)
	
	f = FileReader(local_path)

	hdr = f.readline().rstrip().split("\t")
	hdr_index = {}
	for i, name in enumerate(hdr):
		hdr_index[name] = i

	__COLUMNS = ["gene_name", "gene_sym", "gene_desc", "gene_chr", "gene_band", "gene_strand",
		"gene_pos_start", "gene_pos_end", "gene_biotype", "gene_status", "gene_source",
		"gene_transcript_count", "gene_gc_content"]

	indices = [hdr_index[c] for c in __COLUMNS]

	for id, line in enumerate(f):
		fields = line.rstrip().split("\t")
		ib.insert([id] + [fields[idx] for idx in indices])

	ib.close()

	f.close()
	repo.close_local(local_path)

	rs.close()

task.start()
