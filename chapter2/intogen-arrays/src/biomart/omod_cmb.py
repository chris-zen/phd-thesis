#!/usr/bin/env python

"""
Import ICDO terms into the database

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
"""

from wok.task import Task

from intogen.biomart import biomart_db_connect, DEFAULT_DB_ENGINE

task = Task()

@task.main()
def main():
	task.check_conf(["entities", "repositories", "biomart.db"])
	conf = task.conf

	db_engine = conf.get("biomart.db.engine", DEFAULT_DB_ENGINE)

	log = task.logger()

	conn = biomart_db_connect(conf["biomart.db"], log)

	cursor = conn.cursor()

	log.info("Gain modules ...")

	cursor.execute("""
		create table omod_cmb (
		 cond_id integer not null,
		 icdo_id integer not null,
		 gene_id integer not null,
		 omod_cmb_name varchar(600) not null,
		 primary key (cond_id, icdo_id, gene_id),
		 index (icdo_id, gene_id),
		 index (gene_id),
		 foreign key (cond_id) references ent_condition(cond_id),
		 foreign key (icdo_id) references ent_icdo(id),
		 foreign key (gene_id) references ent_gene(id)
		) ENGINE={}, DEFAULT CHARSET=latin1
		select 1 as cond_id, r.icdo_id, r.gene_id, concat('gain; ', i.icdo_topography, '; ', i.icdo_morphology) as omod_cmb_name
		from cmb_gene_cna r
		left join ent_icdo i on r.icdo_id = i.id
		where gain_pvalue <= 0.05
		order by icdo_id, gene_id""".format(db_engine))

	log.info("Loss modules ...")

	cursor.execute("""
		insert into omod_cmb
		select 2 as cond_id, r.icdo_id, r.gene_id, concat('loss; ', i.icdo_topography, '; ', i.icdo_morphology) as omod_cmb_name
		from cmb_gene_cna r
		left join ent_icdo i on r.icdo_id = i.id
		where loss_pvalue <= 0.05
		order by icdo_id, gene_id""")

	log.info("Upregulation modules ...")

	cursor.execute("""
		insert into omod_cmb
		select 3 as cond_id, r.icdo_id, r.gene_id, concat('upreg; ', i.icdo_topography, '; ', i.icdo_morphology) as omod_cmb_name
		from cmb_gene_trs r
		left join ent_icdo i on r.icdo_id = i.id
		where upreg_pvalue <= 0.05
		order by icdo_id, gene_id""")

	log.info("Downregulation modules ...")

	cursor.execute("""
		insert into omod_cmb
		select 4 as cond_id, r.icdo_id, r.gene_id, concat('downreg; ', i.icdo_topography, '; ', i.icdo_morphology) as omod_cmb_name
		from cmb_gene_trs r
		left join ent_icdo i on r.icdo_id = i.id
		where downreg_pvalue <= 0.05
		order by icdo_id, gene_id""")

	cursor.close()
	conn.close()

task.start()