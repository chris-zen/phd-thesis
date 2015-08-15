#!/usr/bin/env python

"""
Drop tables in the database
"""

from wok.task import Task

from intogen.biomart import biomart_db_connect

task = Task()

@task.main()
def main():
	task.check_conf(["biomart.db"])
	conf = task.conf

	log = task.logger()

	conn = biomart_db_connect(conf["biomart.db"], log)

	cursor = conn.cursor()

	cursor.execute("""DROP TABLE IF EXISTS
		omod_cmb, omod_exp,
		exp_gene_trs, exp_go_trs, exp_kegg_trs, exp_tfbs_trs, exp_mirna_trs,
		cmb_gene_trs, cmb_go_trs, cmb_kegg_trs, cmb_tfbs_trs, cmb_mirna_trs,
		exp_gene_cna, exp_go_cna, exp_kegg_cna, exp_tfbs_cna, exp_mirna_cna,
		cmb_gene_cna, cmb_go_cna, cmb_kegg_cna, cmb_tfbs_cna, cmb_mirna_cna,
		ent_experiment, ent_icdo""")

	cursor.close()
	conn.close()

task.start()

