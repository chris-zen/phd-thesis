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
		create table omod_exp (
		 cond_id integer not null,
		 icdo_id integer not null,
		 exp_id integer not null,
		 gene_id integer not null,
		 omod_exp_name varchar(800) not null,
		 primary key (cond_id, icdo_id, exp_id, gene_id),
		 index (icdo_id, exp_id, gene_id),
		 index (exp_id, gene_id),
		 index (gene_id),
		 foreign key (cond_id) references ent_condition(cond_id),
		 foreign key (icdo_id) references ent_icdo(id),
		 foreign key (exp_id) references ent_experiment(id),
		 foreign key (gene_id) references ent_gene(id)
		) ENGINE={}, DEFAULT CHARSET=latin1
		select 1 as cond_id, r.icdo_id, r.exp_id, r.gene_id, concat('gain; ', i.icdo_topography, '; ', i.icdo_morphology, '; ', e.pub_authors, '; ', e.platf_title) as omod_exp_name
		from exp_gene_cna r
		left join ent_icdo i on r.icdo_id = i.id
		left join ent_experiment e on r.exp_id = e.id
		where gain_pvalue <= 0.05
		order by icdo_id, exp_id, gene_id""".format(db_engine))

	log.info("Loss modules ...")

	cursor.execute("""
		insert into omod_exp
		select 2 as cond_id, r.icdo_id, r.exp_id, r.gene_id, concat('loss; ', i.icdo_topography, '; ', i.icdo_morphology, '; ', e.pub_authors, '; ', e.platf_title) as omod_exp_name
		from exp_gene_cna r
		left join ent_icdo i on r.icdo_id = i.id
		left join ent_experiment e on r.exp_id = e.id
		where loss_pvalue <= 0.05
		order by icdo_id, exp_id, gene_id""")

	log.info("Upregulation modules ...")

	cursor.execute("""
		insert into omod_exp
		select 3 as cond_id, r.icdo_id, r.exp_id, r.gene_id, concat('upreg; ', i.icdo_topography, '; ', i.icdo_morphology, '; ', e.pub_authors, '; ', e.platf_title) as omod_exp_name
		from exp_gene_trs r
		left join ent_icdo i on r.icdo_id = i.id
		left join ent_experiment e on r.exp_id = e.id
		where upreg_pvalue <= 0.05
		order by icdo_id, exp_id, gene_id""")

	log.info("Downregulation modules ...")

	cursor.execute("""
		insert into omod_exp
		select 4 as cond_id, r.icdo_id, r.exp_id, r.gene_id, concat('downreg; ', i.icdo_topography, '; ', i.icdo_morphology, '; ', e.pub_authors, '; ', e.platf_title) as omod_exp_name
		from exp_gene_trs r
		left join ent_icdo i on r.icdo_id = i.id
		left join ent_experiment e on r.exp_id = e.id
		where downreg_pvalue <= 0.05
		order by icdo_id, exp_id, gene_id""")

	cursor.close()
	conn.close()

task.start()