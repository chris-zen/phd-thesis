#!/usr/bin/env python

import uuid

from wok.task import Task

from intogen.data.entity.server import EntityServer
from intogen.data.entity import types

"""
Copy mrna.log2r_source assays into mrna.log2r
without overwriting those created from mrna.absi.

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
- The ones required by intogen.task.Task

* Input:

- mrna_log2r_source_ids: The id's of the mrna.log2r_source assays to be processed. By default all existing will be processed.

* Output:

- Entities: mrna.log2r
"""

def run(task):
	
	# Initialization

	task.check_conf(["entities"])
	conf = task.conf

	log = task.logger()

	task.check_in_ports(["log2r_source_ids"])
	task.check_out_ports(["log2r_ids"])

	log2r_source_port = task.ports["log2r_source_ids"]
	log2r_port = task.ports["log2r_ids"]

	es = EntityServer(conf["entities"])
	em = es.manager()

	# Run

	log.info("Creating indices for mrna log2r assays ...")
	log2r_index = em.group_ids(
		["study_id", "platform_id", "sample_id", "icdo_topography", "icdo_morphology"],
		types.MRNA_LOG2R, unique = True)

	for log2r_source_id in log2r_source_port:
		s = em.find(log2r_source_id, types.MRNA_LOG2R_SOURCE)
		if s is None:
			log.error("%s not found: %s" % (types.MRNA_LOG2R_SOURCE, log2r_source_id))
			continue

		update = True
		key = (s["study_id"], s["platform_id"], s["sample_id"], s["icdo_topography"], s.get("icdo_morphology", ""))
		if key in log2r_index:
			log2r_id = log2r_index[key][0]
			log2r = em.find(log2r_id, types.MRNA_LOG2R)
			if log2r is None:
				log.error("%s not found: %s" % (types.MRNA_LOG2R, log2r_id))
				continue

			update = "absi_id" not in log2r
			if not update:
				log.debug("Not copying log2r %s already calculated from absi %s" % (log2r_source_id, log2r["absi_id"]))
				continue
		else:
			log2r_id = str(uuid.uuid4())
			log2r = s.transform([
				"study_id", "platform_id", "sample_id", "icdo_topography", "icdo_morphology",
				"data_file/repo", "data_file/path", "data_file/name"])
			log2r["id"] = log2r_id

		log2r["log2r_source_id"] = log2r_source_id

		log.debug("Persisting log2r assay %s ..." % log2r_id)
		em.persist(log2r, types.MRNA_LOG2R)

		log2r_port.write(log2r_id)

	em.close()

if __name__ == "__main__":
	Task(run).start()
