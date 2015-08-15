#!/usr/bin/env python

import re
import uuid

from wok.task import Task
from wok.element import DataElement

from intogen.data.entity.server import EntityServer
from intogen.data.entity import types

"""
Classify mrna.log2r assays into mrna.log2r_tumour_unit's by
- study_id
- platform_id
- icdo_topography
- icdo_morphology

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
- overwrite: (optional) Overwrite already existing pool data files ?. Default = no
- mrna.min_tumour_unit_size: (optional) The minimum number of log2r assays of a unit

* Input:

- log2r_ids: The mrna.log2r ids to process

* Output:

- log2r_tumour_unit_ids: The ids of the new mrna.log2r_tumour_unit's created
    (only the ones with more or equal number of log2r assays than mrna.min_tumour_unit_size)

* Entities:

- mrna.log2r (R)
- mrna.log2r_tumour_unit (R/W)

"""

_ICDO_TOPOGRAPHY_PAT = re.compile(r"^(C\d\d)(.\d)?$")
_ICDO_MORPHOLOGY_PAT = re.compile(r"^\d\d\d\d(/\d)?$")

def run(task):

	# Initialization

	task.check_conf(["entities", "repositories", "repositories.assay"])
	conf = task.conf

	min_tumour_unit_size = conf.get("mrna.min_tumour_unit_size", 20, dtype=int)

	log = task.logger()

	task.check_in_ports(["log2r_ids"])
	task.check_out_ports(["log2r_tumour_unit_ids"])

	log2r_port = task.ports["log2r_ids"]
	log2r_tumour_unit_port = task.ports["log2r_tumour_unit_ids"]

	es = EntityServer(conf["entities"])
	em = es.manager()

	overwrite = conf.get("overwrite", False, dtype=bool)

	if "excluded_topographies" in conf:
		excluded_topographies = set(conf.get("excluded_topographies"))
		log.debug("Excluded topographies: {}".format(", ".join(excluded_topographies)))
	else:
		excluded_topographies = set()
		
	# Run

	log.info("Indexing available mrna log2r tumour units ...")
	log2r_tumour_unit_index = em.group_ids(
		["study_id", "platform_id", "icdo_topography", "icdo_morphology"],
		types.MRNA_LOG2R_TUMOUR_UNIT, unique = True)

	units = {}
	for log2r_id in log2r_port:
		e = em.find(log2r_id, types.MRNA_LOG2R)
		if e is None:
			log.error("%s not found: %s" % (types.MRNA_LOG2R, log2r_id))
			continue

		eid = e["id"]
		study_id = e["study_id"]
		platform_id = e["platform_id"]
		icdo_topography = e["icdo_topography"]
		icdo_morphology = e.get("icdo_morphology", "")
		
		log.info("Classifying mrna log2r (%s, %s, %s, %s) [%s] ..." % (study_id, platform_id, icdo_topography, icdo_morphology, eid))
		
		keys = []
	
		m = _ICDO_TOPOGRAPHY_PAT.match(icdo_topography)
		if m is None:
			log.error("Wrong ICD-O Topography code: {0}".format(icdo_topography))
			continue
		else:
			level1 = m.group(1)
			level2 = m.group(2)

		if len(icdo_morphology) > 0:
			m = _ICDO_MORPHOLOGY_PAT.match(icdo_morphology)
			if m is None:
				log.error("Wrong ICD-O Morphology code: {0}".format(icdo_morphology))
				continue

		keys += [(study_id, platform_id, level1, "")]
		if len(icdo_morphology) > 0:
			keys += [(study_id, platform_id, level1, icdo_morphology)]
			#keys += [(study_id, platform_id, "", icdo_morphology)]
	
		if level2 is not None:
			keys += [(study_id, platform_id, icdo_topography, "")]
			if len(icdo_morphology) > 0:
				keys += [(study_id, platform_id, icdo_topography, icdo_morphology)]

		for key in keys:
			icdo_topography = key[2]
			if icdo_topography in excluded_topographies:
				log.debug("\t(%s) [excluded]" % ", ".join(key))
				continue

			log.debug("\t(%s)" % ", ".join(key))
			
			if key not in units:
				units[key] = [eid]
			else:
				units[key] += [eid]

	log.info("Persisting %i mrna log2r tumour units ..." % len(units))
	log.debug("Minimum size = %i" % min_tumour_unit_size)

	for key, ids in sorted(units.iteritems()):
		
		size = len(ids)
		
		if size < min_tumour_unit_size:
			log.debug("\t(%s)\t%i assays [Skipped]" % (", ".join(key), size))
			continue
		else:
			log.debug("\t(%s)\t%i assays" % (", ".join(key), size))

		if key in log2r_tumour_unit_index:
			uid = log2r_tumour_unit_index[key][0]
			if not overwrite:
				u = em.find(uid, types.MRNA_LOG2R_TUMOUR_UNIT)
			else:
				u = DataElement(key_sep = "/")
		else:
			uid = str(uuid.uuid4())
			u = DataElement(key_sep = "/")

		u["id"] = uid
		u["study_id"] = key[0]
		u["platform_id"] = key[1]
		u["icdo_topography"] = key[2]
		u["icdo_morphology"] = key[3]

		u["size"] = size
		u["mrna_log2r_ids"] = u.create_list(ids)
		
		em.persist(u, types.MRNA_LOG2R_TUMOUR_UNIT)
		log2r_tumour_unit_port.write(uid)
	
	em.close()
	es.close()

if __name__ == "__main__":
	Task(run).start()
