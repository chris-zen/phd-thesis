#!/usr/bin/env python

"""
Classify oncodrive gene results and prepare for combination

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory

* Input:

- oncodrive_ids: The mrna.oncodrive_genes to process

* Output:

- combinations: The mrna.combination prepared to be calculated

* Entities:

- mrna.oncodrive_genes
- mrna.combination

"""

import uuid
import json

from wok.task import Task
from wok.element import DataElement

from intogen.data.entity.server import EntityServer
from intogen.data.entity import types

def run(task):

	# Initialization

	task.check_conf(["entities"])
	conf = task.conf

	log = task.logger()

	task.check_in_ports(["oncodrive_ids"])
	task.check_out_ports(["combinations"])

	oncodrive_port = task.ports["oncodrive_ids"]
	combination_port = task.ports["combinations"]

	es = EntityServer(conf["entities"])
	em = es.manager()

	log.info("Indexing available combination results ...")
	comb_results_index = em.group_ids(
		["icdo_topography", "icdo_morphology", "id_type"],
		types.MRNA_COMBINATION, unique = True)

	ENSEMBL_GENE = "ensembl:gene"

	classif = {}

	log.info("Classifying oncodrive results ...")

	for oid in oncodrive_port:
		o = em.find(oid, types.MRNA_ONCODRIVE_GENES)
		if o is None:
			log.error("{0} not found: {1}".format(types.MRNA_ONCODRIVE_GENES, oid))
			continue

		okey = (o["study_id"], o["platform_id"], o["icdo_topography"], o["icdo_morphology"])

		key = (o["icdo_topography"], o["icdo_morphology"], ENSEMBL_GENE)

		log.debug("Oncodrive results ({0}) [{1}] classified into ({2}) ...".format(", ".join(okey), oid, ", ".join(key)))

		if key in classif:
			classif[key] += [o]
		else:
			classif[key] = [o]

	log.info("Preparing combinations ...")

	for key in sorted(classif):
		if key in comb_results_index:
			cid = comb_results_index[key][0]
			c = em.find(cid, types.MRNA_COMBINATION)
			if c is None:
				log.error("{0} not found: {1}".format(types.MRNA_COMBINATION, cid))
				return
		else:
			c = DataElement(key_sep = "/")
			c["id"] = cid = str(uuid.uuid4())
			c["icdo_topography"] = key[0]
			c["icdo_morphology"] = key[1]

		c["id_type"] = ENSEMBL_GENE

		olist = classif[key]
		
		log.info("({0}) [{1}] --> {2} results".format(", ".join(key), cid, len(olist)))

		ids = c.create_list()
		flist = c.create_list()

		for o in olist:
			ids += [o["id"]]
			flist += [o["results_file"]]

		c["source"] = src = c.create_element()
		src["type"] = types.MRNA_ONCODRIVE_GENES
		src["ids"] = ids

		c["files"] = flist

		combination_port.write(json.dumps(c.to_native()))

	em.close()

if __name__ == "__main__":
	Task(run).start()
