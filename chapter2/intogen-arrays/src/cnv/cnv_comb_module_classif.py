#!/usr/bin/env python

"""
Classify enrichment results and prepare for combination

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory

* Input:

- enrichment_ids: The cnv.enrichment to process

* Output:

- combinations: The cnv.combination prepared to be calculated

* Entities:

- cnv.enrichment
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

	enrichment_port, combination_port = \
		task.ports("enrichment_ids", "combinations")

	es = EntityServer(conf["entities"])
	em = es.manager()

	log.info("Indexing available {} results ...".format(types.CNV_COMBINATION))
	comb_results_index = em.group_ids(
		["icdo_topography", "icdo_morphology", "id_type"],
		types.CNV_COMBINATION, unique = True)

	classif = {}

	log.info("Classifying enrichment results ...")

	for eid in enrichment_port:
		e = em.find(eid, types.CNV_ENRICHMENT)
		if e is None:
			log.error("{} not found: {}".format(types.CNV_ENRICHMENT, eid))
			continue

		ekey = (e["study_id"], e["platform_id"], e["icdo_topography"], e["icdo_morphology"], e["id_type"])

		key = (e["icdo_topography"], e["icdo_morphology"], e["id_type"])

		log.debug("Enrichment results ({}) [{}] classified into ({}) ...".format(", ".join(ekey), eid, ", ".join(key)))

		if key in classif:
			classif[key] += [e]
		else:
			classif[key] = [e]

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
			c["id_type"] = key[2]

		elist = classif[key]
		
		log.info("({}) [{}] --> {} results".format(", ".join(key), cid, len(elist)))

		ids = c.create_list()
		flist = c.create_list()

		for e in elist:
			ids += [e["id"]]
			flist += [e["results_file"]]

		c["source"] = src = c.create_element()
		src["type"] = types.CNV_ENRICHMENT
		src["ids"] = ids

		c["files"] = flist

		combination_port.write(c.to_native())

	em.close()
	es.close()

task.start()
