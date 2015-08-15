#!/usr/bin/env python

"""
Get gene data from ensembl

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory

"""

from wok.task import Task

from biomart import BiomartService

# Initialization

task = Task()

@task.main()
def main():
	conf = task.conf

	log = task.logger()

	query = """
		<?xml version="1.0" encoding="UTF-8"?>
		<!DOCTYPE Query>
		<Query  virtualSchemaName = "default" formatter = "TSV" header = "0" uniqueRows = "1" count = "" datasetConfigVersion = "0.6" >
			<Dataset name = "hsapiens_gene_ensembl" interface = "default" >
				<Attribute name = "ensembl_gene_id" />
				<Attribute name = "external_gene_id" />
				<Attribute name = "description" />
				<Attribute name = "chromosome_name" />
				<Attribute name = "band" />
				<Attribute name = "strand" />
				<Attribute name = "start_position" />
				<Attribute name = "end_position" />
				<Attribute name = "gene_biotype" />
				<Attribute name = "status" />
				<Attribute name = "source" />
				<Attribute name = "transcript_count" />
				<Attribute name = "percentage_gc_content" />
			</Dataset>
		</Query>"""

	bs = BiomartService(
		conf["biomart.host"],
		conf.get("biomart.port"),
		conf.get("biomart.path"))

	log.info("Connecting to biomart ...")

	bs.connect()

	#TODO path, local_path

	log.info("Creating file {0} ...".format(path))

	f = FileWriter(local_path)

	f.write("\t".join(["gene_name", "gene_sym", "gene_desc", "gene_chr", "gene_band", "gene_strand",
		"gene_pos_start", "gene_pos_end", "gene_biotype", "gene_status", "gene_source",
		"gene_transcript_count", "gene_gc_content"]))
	f.write("\n")

	count = 0
	for line in bs.query(query):
		f.write(line)

		if count % 10000:
			log.debug("{0} rows".format(count))
		count += 1

	f.close()
	bs.close()

task.start()
