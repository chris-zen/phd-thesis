#!/usr/bin/env python

"""
Classify oncodrive gene results and prepare for combination

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory

* Input:

- oncodrive_ids: The cnv.oncodrive_genes to process

* Output:

- combinations: The cnv.combination prepared to be calculated

* Entities:

- cnv.oncodrive_genes
- cnv.combination
"""

import uuid

from wok.task import Task
from wok.element import DataElement

from intogen.data.entity.server import EntityServer
from intogen.data.entity import types

task = Task()

@task.main()
def main():

	# Initialization

	task.check_conf(["entities"])
	conf = task.conf

	log = task.logger()

	oncodrive_port, combination_port = \
		task.ports("oncodrive_ids", "combinations")

	es = EntityServer(conf["entities"])
	em = es.manager()

	log.info("Indexing available {} results ...".format(types.CNV_COMBINATION))
	comb_results_index = em.group_ids(
		["icdo_topography", "icdo_morphology", "id_type"],
		types.CNV_COMBINATION, unique = True)

	ENSEMBL_GENE = "ensembl:gene"

	classif = {}

	log.info("Classifying oncodrive results ...")

	for oid in oncodrive_port:
		o = em.find(oid, types.CNV_ONCODRIVE_GENES)
		if o is None:
			log.error("{} not found: {}".format(types.CNV_ONCODRIVE_GENES, oid))
			continue

		okey = (o["study_id"], o["platform_id"], o["icdo_topography"], o["icdo_morphology"])

		key = (o["icdo_topography"], o["icdo_morphology"], ENSEMBL_GENE)

		log.debug("Oncodrive results ({}) [{}] classified into ({}) ...".format(", ".join(okey), oid, ", ".join(key)))

		if key in classif:
			classif[key] += [o]
		else:
			classif[key] = [o]

	log.info("Preparing combinations ...")

	for key in sorted(classif):
		if key in comb_results_index:
			cid = comb_results_index[key][0]
			c = em.find(cid, types.CNV_COMBINATION)
			if c is None:
				log.error("{} not found: {}".format(types.CNV_COMBINATION, cid))
				return
		else:
			c = DataElement(key_sep = "/")
			c["id"] = cid = str(uuid.uuid4())
			c["icdo_topography"] = key[0]
			c["icdo_morphology"] = key[1]

		c["id_type"] = ENSEMBL_GENE

		olist = classif[key]
		
		log.info("({}) [{}] --> {} results".format(", ".join(key), cid, len(olist)))

		ids = c.create_list()
		flist = c.create_list()

		for o in olist:
			ids += [o["id"]]
			flist += [o["results_file"]]

		c["source"] = src = c.create_element()
		src["type"] = types.CNV_ONCODRIVE_GENES
		src["ids"] = ids

		c["files"] = flist

		combination_port.write(c.to_native())

	em.close()
	es.close()

task.start()
