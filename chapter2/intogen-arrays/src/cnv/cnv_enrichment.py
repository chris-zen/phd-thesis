#!/usr/bin/env python

"""
Calculate enrichment of the oncodrive results

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
- repositories.data: The path to the repository where data files are written.
- overwrite: (optional) Overwrite already existing files ?. Default = no
- bin_paths.gitools: Path to gitools

* Input:

- oncodrive_ids: The cnv.oncodrive_genes to process

* Output:

- enrichment_ids: The ids of the created cnv.enrichment

* Entities:

- cnv.oncodrive_genes
- cnv.enrichment
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

task = Task()

@task.main()
def main():

	# Initialization

	task.check_conf(["entities", "repositories", "repositories.data", "repositories.source",
						"cnv.enrichment", "bin_paths.gitools"])
	conf = task.conf

	log = task.logger()

	oncodrive_port, enrichment_port = \
		task.ports("oncodrive_ids", "enrichment_ids")

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])

	data_repo = rs.repository("data")
	
	overwrite = conf.get("overwrite", False, dtype=bool)

	# retrieve enrichment configurations
	ec = conf["cnv.enrichment"]
	if "default" in ec:
		default = ec["default"]
	else:
		default = conf.create_element()

	if "modules" not in ec:
		log.error("There is no enrichment modules section available in cnv.enrichment")
		return -1

	log.info("Reading modules configuration ...")

	econfs = list()
	for mod in ec["modules"]:
		m = ec.create_element()
		m.merge(default)
		m.merge(mod)
		mf = m.missing_fields(["id_type", "test", "modules_file"])
		if len(mf) > 0:
			log.error("Enrichment configuration missing required fields: {0}".format(", ".join(mf)))
			log.error("Module configuration: {}".format(m))
		else:
			econfs.append(m)
			log.debug("{} -> {}".format(m["id_type"], m["modules_file"]))

	if len(econfs) == 0:
		log.error("There are no enrichment configurations available in cnv.enrichment")
		return 0

	results_base_path = types.CNV_ENRICHMENT.replace(".", "/")
	
	log.info("Indexing available {} results ...".format(types.CNV_ENRICHMENT))
	enrichment_results_index = em.group_ids(
		["study_id", "platform_id", "icdo_topography", "icdo_morphology", "id_type"],
		types.CNV_ENRICHMENT, unique = True)

	for oid in oncodrive_port:
		o = em.find(oid, types.CNV_ONCODRIVE_GENES)
		if o is None:
			log.error("{0} not found: {1}".format(types.CNV_ONCODRIVE_GENES, oid))
			continue

		okey = (o["study_id"], o["platform_id"], o["icdo_topography"], o["icdo_morphology"])

		log.info("Enrichment for oncodrive results ({}) [{}] ...".format(", ".join(okey), oid))

		for ec in econfs:
			log.info("Module {} [{}] ...".format(ec["id_type"], ec["modules_file"]))

			key = (o["study_id"], o["platform_id"], o["icdo_topography"], o["icdo_morphology"], ec["id_type"])

			if key in enrichment_results_index:
				eid = enrichment_results_index[key][0]
				e = em.find(eid, types.CNV_ENRICHMENT)
				if e is None:
					log.error("{} not found: {}".format(types.CNV_ENRICHMENT, eid))
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
						["id", "gain_corrected_right_p_value", "loss_corrected_right_p_value"],
						["id", "gain", "loss"])

			# save mapped results
			if valid:
				em.persist(e, types.CNV_ENRICHMENT)
				enrichment_port.write(eid)

	em.close()
	es.close()
	data_repo.close()
	rs.close()

task.start()
