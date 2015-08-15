#!/usr/bin/env python

"""
Calculate enrichment of the oncodrive results

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
- repositories.data: (optional) The path to the repository where data files are written. Default value = work.path
- overwrite: (optional) Overwrite already existing files ?. Default = no
- bin_paths.gitools: Path to gitools

* Input:

- oncodrive_ids: The mrna.oncodrive_genes to process

* Output:

- enrichment_ids: The ids of the created mrna.enrichment

* Entities:

- mrna.oncodrive_genes
- mrna.enrichment

"""

import uuid

from wok.task import Task
from wok.element import DataElement

from intogen.utils import skip_file
from intogen.repository import rpath
from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.data.entity import types
from intogen.enrichment import enrichment

def run(task):

	# Initialization

	task.check_conf(["entities", "repositories", "repositories.data", "repositories.source",
						"mrna.enrichment", "bin_paths.gitools"])
	conf = task.conf

	log = task.logger()

	task.check_in_ports(["oncodrive_ids"])
	task.check_out_ports(["enrichment_ids"])

	oncodrive_port = task.ports["oncodrive_ids"]
	enrichment_port = task.ports["enrichment_ids"]

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])

	data_repo = rs.repository("data")
	
	overwrite = conf.get("overwrite", False, dtype=bool)

	# retrieve enrichment configurations
	ec = conf["mrna.enrichment"]
	if "default" in ec:
		default = ec["default"]
	else:
		default = conf.create_element()

	if "modules" not in ec:
		log.error("There is no enrichment modules section available in mrna.enrichment")
		return -1

	log.info("Reading modules configuration ...")

	econfs = list()
	for mod in ec["modules"]:
		m = ec.create_element()
		m.merge(default)
		m.merge(mod)
		mf = m.missing_fields(["id_type", "test", "modules_file"])
		if len(mf) > 0:
			log.error("Enrichment configuration missing required fields: {}".format(", ".join(mf)))
			log.error("Module configuration: {}".format(m))
		else:
			econfs.append(m)
			log.debug("{} -> {}".format(m["id_type"], m["modules_file"]))

	if len(econfs) == 0:
		log.error("There are no enrichment configurations available in mrna.enrichment")
		return 0

	results_base_path = types.MRNA_ENRICHMENT.replace(".", "/")
	
	log.info("Indexing available enrichment results ...")
	enrichment_results_index = em.group_ids(
		["study_id", "platform_id", "icdo_topography", "icdo_morphology", "id_type"],
		types.MRNA_ENRICHMENT, unique = True)

	for oid in oncodrive_port:
		o = em.find(oid, types.MRNA_ONCODRIVE_GENES)
		if o is None:
			log.error("{0} not found: {1}".format(types.MRNA_ONCODRIVE_GENES, oid))
			continue

		okey = (o["study_id"], o["platform_id"], o["icdo_topography"], o["icdo_morphology"])

		log.info("Enrichment for oncodrive results ({0}) [{1}] ...".format(", ".join(okey), oid))

		for ec in econfs:
			log.info("Module {} [{}] ...".format(ec["id_type"], ec["modules_file"]))

			key = (o["study_id"], o["platform_id"], o["icdo_topography"], o["icdo_morphology"], ec["id_type"])

			if key in enrichment_results_index:
				eid = enrichment_results_index[key][0]
				e = em.find(eid, types.MRNA_ENRICHMENT)
				if e is None:
					log.error("{} not found: {}".format(types.MRNA_ENRICHMENT, eid))
					continue
			else:
				e = o.transform(["study_id", "platform_id", "icdo_topography", "icdo_morphology"])
				e["id"] = eid = str(uuid.uuid4())

			e["id_type"] = ec["id_type"]

			# enrichment results

			results_path = rpath.join(results_base_path, eid + ".tsv.gz")

			if skip_file(overwrite, data_repo, results_path, e.get("results_file")):
				log.warn("Skipping ({}) [{}] as it already exists".format(", ".join(key), eid))
				enrichment_port.write(eid)
				continue

			valid = enrichment(log, conf, rs, data_repo, results_path, o["results_file"], e, ec,
						["id", "upreg_corrected_right_p_value", "downreg_corrected_right_p_value"],
						["id", "upreg", "downreg"])

			# save mapped results
			if valid:
				em.persist(e, types.MRNA_ENRICHMENT)
				enrichment_port.write(eid)

	em.close()
	es.close()
	data_repo.close()
	rs.close()

if __name__ == "__main__":
	Task(run).start()
