#!/usr/bin/env python

"""
Create cnv.evt assays from source.assay with:
- assay_design = cancer_and_normal
- data_type = log_abs_intensities
- study_type = transcriptomic
and classify them into cnv.absi_tumour_unit

* Configuration parameters:

- The ones required by intogen.data.entity.EntityServer
- repositories.assay: The path to the repository where the assay data files are

* Input:

- study_ids: The study ids to process.

* Output:

- evt_ids: generated evt ids
- evt_tumour_unit_ids: generated evt_tumour_unit ids

* Entities:

- cnv.evt, cnv.evt_tumour_unit
"""

import uuid

from wok.task import Task
from wok.element import DataElement
from intogen.utils import classify_by_experiment_and_icdo
from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.data.entity import types

def map_inc(m, key):
	if key not in m:
		m[key] = 1
	else:
		m[key] += 1

def map_list_add(m, key, value):
	if key not in m:
		m[key] = [value]
	else:
		m[key] += [value]

def map_count_tostring(m, indent = 0):
	sb = []
	for k, v in m.items():
		sb += ["\t" * indent]
		sb += ["%s\t --> %i\n" % (k, v)]
	sb += ["\n"]
	return "".join(sb)

def map_list_tostring(m, indent = 0):
	sb = []
	for k, v in sorted(m.items()):
		sb += ["\t" * indent]
		sb += [">>> %s\n\n" % k]
		sb += ["\t" * (indent + 1)]
		sb += ["[ %s ]\n\n" % (", ".join(sorted(v)))]
	return "".join(sb)

disease_state_map = {
	"primary_sample" : "tumour",
	"metastasis_sample" : "ignore",
	"recurrence_sample" : "ignore",
	"cell_line" : "ignore",
	"normal_paired" : "normal",
	"normal_control" : "normal"
}

task = Task()

@task.main()
def main():

	# Initialization

	task.check_conf(["entities", "repositories", "repositories.assay",
				"cnv.min_tumour_unit_size"])

	conf = task.conf

	log = task.logger()

	study_ids_port, evt_port, evt_tunit_port = \
		task.ports("study_ids", "evt_ids", "evt_tumour_unit_ids")
	
	es = EntityServer(conf["entities"])
	em = es.manager()
	
	rs = RepositoryServer(conf["repositories"])
	source_repo = rs.repository("source")

	if "excluded_topographies" in conf:
		excluded_topographies = set(conf.get("excluded_topographies"))
		log.debug("Excluded topographies: {}".format(", ".join(excluded_topographies)))
	else:
		excluded_topographies = set()
		
	# Run

	log.info("Creating indices for {} ...".format(types.CNV_EVENTS))
	evt_index = em.group_ids(
		["study_id", "platform_id", "sample_id", "icdo_topography", "icdo_morphology"],
		types.CNV_EVENTS, unique = True)
	
	log.info("Creating indices for {} ...".format(types.CNV_EVENTS_TUMOUR_UNIT))
	evt_tunit_index = em.group_ids(
		["study_id", "platform_id", "icdo_topography", "icdo_morphology"],
		types.CNV_EVENTS_TUMOUR_UNIT, unique = True)
	
	processed_studies = set()
	processed_assays = 0
	valid_assay_count = {}
	skipped_assay_count = {}
	wrong_assays = {}
	wrong_samples = {}
	tumour_units = {}
	evt_dup = {}
	
	study_ids = study_ids_port.read_all()
	log.info("Processing %i studies ..." % len(study_ids))

	for assay in em.iter_all(types.SOURCE_ASSAY):

		assay_id = assay.get("id", "WITHOUT ID")
		log.debug("Reading assay %s ..." % assay_id)

		mf = assay.missing_fields(["id", "study_id", "platform_id", "sample_id",
			"assay_property/assay_design", "assay_property/data_type",
			"assay_property/study_type", "assay_property/filename"])	
		
		assay_source_path = assay.get("source_path", "")
		
		if len(mf) > 0:
			study_id = assay.get("study_id", "WITHOUT ID")
			doc_path = assay.get("__doc_path", "UNKNOWN")

			log.error("Assay {} in study {} missing required fields: ({}) ({})".format(assay_id, study_id, ", ".join(mf), assay_source_path))
			map_list_add(wrong_assays, study_id, assay_id)
			continue

		study_id = assay["study_id"]

		if study_id not in study_ids:
			log.debug("Assay {} not included in 'study_ids'".format(assay_id))
			continue

		platform_id = assay["platform_id"]
		sample_id = assay["sample_id"]
		
		assay_design = assay["assay_property/assay_design"]
		data_type = assay["assay_property/data_type"]
		study_type = assay["assay_property/study_type"]

		source_path = assay["source_path"]
		source_file = assay["assay_property/filename"]

		e = assay.transform([
			("assay_id", "id"),
			"study_id",
			"platform_id",
			"sample_id",
			"source_path"])

		e["data_file"] = source_repo.url("assay", source_path, source_file)

		included = study_id in study_ids and study_type == "genomic"
		included &= (assay_design == "cancer_vs_normal" and data_type == "binary")

		if not included:
			if study_type != "transcriptomic" and study_id in study_ids:
				s = ", ".join([" = ".join(v) for v in [("study_id", study_id), ("assay_design", assay_design), ("data_type", data_type), ("study_type", study_type)]])
				log.debug("Skipping assay {} ({}): {}.".format(assay_id, assay_source_path, s))
				map_inc(skipped_assay_count, (study_id, assay_design, data_type, study_type))
			continue

		sample = em.find(sample_id, types.SOURCE_SAMPLE)
		if sample is None:
			log.error("Assay {} references a non-existent sample: {}".format(assay_id, sample_id))
			map_list_add(wrong_assays, study_id, assay_id)
			continue
		
		mf = sample.missing_fields(["id", "basic_sample_details/disease_state", "icdo/topography"])
		if len(mf) > 0:
			sample_source_path = sample.get("source_path", "")
			log.error("Sample {} associated with assay {} in study {} missing required fields: ({}) ({})".format(sample_id, assay_id, study_id, ", ".join(mf), sample_source_path))
			map_list_add(wrong_samples, study_id, sample_id)
			continue

		sample = sample.transform([
			"id",
			"source_path",
			("disease_state", "basic_sample_details/disease_state"),
			("normal_counterpart", "normal_counterpart_location/topography"),
			("icdo_topography", "icdo/topography"),
			("icdo_morphology", "icdo/morphology") ])
		
		disease_state = sample["disease_state"]
		if disease_state not in disease_state_map:
			log.error("Unknown disease_state '{}' for sample {} ({})".format(disease_state, sample_id, sample.get("source_path", "")))
			map_list_add(wrong_samples, study_id, sample_id)
			continue

		orig_disease_state = disease_state
		disease_state = disease_state_map[disease_state]
		if disease_state not in ["tumour"]:
			log.warn("Sample {} associated with assay {} in study {} has not a tumour 'disease_state' ({}): {}".format(sample_id, assay_id, study_id, sample_source_path, orig_disease_state))
			continue

		e["disease_state"] = disease_state
		
		e["icdo_topography"] = sample["icdo_topography"]
		e["icdo_morphology"] = sample.get("icdo_morphology", "")
		if "normal_counterpart" in sample:
			e["normal_counterpart"] = sample["normal_counterpart"]

		repo, rel_path = rs.from_url(e["data_file"])

		if not repo.exists(rel_path):
			log.error("Assay {} in study {} missing data file: [{}]".format(assay_id, study_id, rel_path))
			map_list_add(wrong_assays, study_id, assay_id)
			continue

		e_key = (study_id, platform_id, sample_id, e["icdo_topography"], e["icdo_morphology"])

		eid = None
		duplicated = False
		exists = False
		if e_key in evt_dup:
			duplicated = True
		elif e_key in evt_index:
			eid = evt_index[e_key][0]
			exists = True
		
		if duplicated:
			log.error("Duplicated key ({}) for assay {}".format(", ".join(e_key), assay_id))
			map_list_add(wrong_assays, study_id, assay_id)
			continue

		if eid is None:
			eid = str(uuid.uuid4())
		
		e["id"] = eid

		u_key = (study_id, platform_id, e.get("normal_counterpart", e["icdo_topography"]), e.get("icdo_morphology", ""))
		keys = classify_by_experiment_and_icdo(
					u_key[0], u_key[1], u_key[2], u_key[3])
		for key in keys:
			icdo_topography = key[2]
			if icdo_topography in excluded_topographies:
				continue
			map_list_add(tumour_units, key, eid)

		processed_studies.add(study_id)
		processed_assays += 1
		map_inc(valid_assay_count, (study_id, platform_id))

		msg = {True : "Overwritting", False : "Writting"}[exists]
		log.info("{} {} ({}) ...".format(msg, types.CNV_EVENTS, ", ".join(e_key)))
		em.persist(e, types.CNV_EVENTS)
		evt_port.write(eid)
		evt_dup[e_key] = eid

	min_tumour_unit_size = conf["cnv.min_tumour_unit_size"]

	log.info("Persisting {} ...".format(types.CNV_EVENTS_TUMOUR_UNIT))
	log.debug("Minimum size = {}".format(min_tumour_unit_size))

	for key in sorted(tumour_units):
		v = tumour_units[key]
		size = len(v)
		if size < min_tumour_unit_size:
			discard = True
			discard_text = "[skipped]"
		else:
			discard = False
			discard_text = ""

		if key in evt_tunit_index:
			uid = evt_tunit_index[key][0]
			u = em.find(uid, types.CNV_EVENTS_TUMOUR_UNIT)
			if u is None:
				log.error("{} not found: {}".format(types.CNV_EVENTS_TUMOUR_UNIT, uid))
				continue

			arrow_text = "==>"
		else:
			uid = str(uuid.uuid4())
			u = DataElement(key_sep = "/")
			u["id"] = uid
			u["study_id"] = key[0]
			u["platform_id"] = key[1]
			u["icdo_topography"] = key[2]
			u["icdo_morphology"] = key[3]

			arrow_text = "-->"

		log.info("\t[{}] ({})\t{} {} assays {}".format(uid, ", ".join(key), arrow_text, size, discard_text))

		if discard:
			continue

		u["size"] = len(v)
		u["cnv_evt_ids"] = u.create_list(v)

		em.persist(u, types.CNV_EVENTS_TUMOUR_UNIT)
		evt_tunit_port.write(uid)

	sb = ["Processed {} assays for {} studies (out of {}):\n\n".format(processed_assays, len(processed_studies), len(study_ids))]
	log.info("".join(sb))

	log.info("Skipped assays:\n\n{}".format(map_count_tostring(skipped_assay_count, indent = 1)))
	
	log.info("Summary of failed assays:\n\n{}".format(map_list_tostring(wrong_assays)))
	
	log.info("Summary of failed samples:\n\n{}".format(map_list_tostring(wrong_samples)))

	em.close()
	es.close()

task.start()
