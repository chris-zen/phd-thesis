#!/usr/bin/env python

"""
Create mrna.absi assays from source.assay with:
- assay_design = cancer_and_normal
- data_type = log_abs_intensities
- study_type = transcriptomic
and classify them into mrna.normal_pool and mrna.absi_tumour_unit

It also creates mrna.log2r from source.assay with:
- assay_design = cancer_vs_normal
- data_type = log2ratios
- study_type = transcriptomic

* Configuration parameters:

- The ones required by intogen.data.entity.EntityServer
- repositories.assay: The path to the repository where the assay data files are

* Input:

- study_ids: The study ids to process.

* Output:

- absi_ids: generated absi ids
- absi_tumour_unit_ids: generated absi_tumour_unit ids
- normal_pool_ids: generated normal_pool ids
- log2r_source_ids: generated log2r_source ids

* Entities:

- mrna.absi, mrna.absi_tumour_unit, mrna.normal_pool, mrna.log2r_source
"""

import os
import uuid

from wok.task import Task
from wok.element import DataElement
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
	
def run(task):

	# Initialization

	task.check_conf(["entities", "repositories", "repositories.assay"])
	conf = task.conf

	log = task.logger()
	
	task.check_in_ports(["study_ids"])
	task.check_out_ports(["absi_ids", "absi_tumour_unit_ids", "normal_pool_ids", "log2r_source_ids"])

	study_ids_port = task.ports["study_ids"]
	absi_port = task.ports["absi_ids"]
	absi_tumour_unit_port = task.ports["absi_tumour_unit_ids"]
	normal_pool_port = task.ports["normal_pool_ids"]
	log2r_source_port = task.ports["log2r_source_ids"]

	es = EntityServer(conf["entities"])
	em = es.manager()
	
	rs = RepositoryServer(conf["repositories"])

	#overwrite = conf.get("overwrite", False, dtype=bool)

	# Run
	
	log.info("Creating indices for {} ...".format(types.MRNA_ABS_INTENSITY))
	absi_index = em.group_ids(
		["study_id", "platform_id", "sample_id", "icdo_topography", "icdo_morphology"],
		types.MRNA_ABS_INTENSITY, unique = True)
	
	log.info("Creating indices for {} ...".format(types.MRNA_LOG2R_SOURCE))
	log2r_src_index = em.group_ids(
		["study_id", "platform_id", "sample_id", "icdo_topography", "icdo_morphology"],
		types.MRNA_LOG2R_SOURCE, unique = True)

	log.info("Creating indices for {} ...".format(types.MRNA_ABSI_TUMOUR_UNIT))
	absi_tumour_unit_index = em.group_ids(
		["study_id", "platform_id", "icdo_topography"],
		types.MRNA_ABSI_TUMOUR_UNIT, unique = True)

	processed_studies = set()
	processed_assays = 0
	valid_assay_count = {}
	skipped_assay_count = {}
	wrong_assays = {}
	wrong_samples = {}
	log2r_src_units = {}
	tumour_units = {}
	normal_pools = {}
	absi_dup = {}
	log2r_source_dup = {}

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

			log.error("Assay %s in study %s missing required fields: %s {%s}" % (assay_id, study_id, mf, assay_source_path))
			map_list_add(wrong_assays, study_id, assay_id)
			continue

		study_id = assay["study_id"]

		if study_id not in study_ids:
			log.debug("Assay %s not included in 'study_ids'" % assay_id)
			continue

		platform_id = assay["platform_id"]
		sample_id = assay["sample_id"]
		
		assay_design = assay["assay_property/assay_design"]
		data_type = assay["assay_property/data_type"]
		study_type = assay["assay_property/study_type"]
		
		e = assay.transform([
			("assay_id", "id"),
			"study_id",
			"platform_id",
			"sample_id",
			"source_path",
			("data_file/path", "source_path"),
			("data_file/name", "assay_property/filename") ])

		e["data_file/repo"] = assay.get("data_file/repo", "assay")

		included = study_id in study_ids and study_type == "transcriptomic"
		included &= (assay_design == "cancer_and_normal" and data_type == "log_abs_readings") \
						or (assay_design == "cancer_vs_normal" and data_type == "log2ratios")

		if not included:
			if study_type != "genomic" and study_id in study_ids:
				s = ", ".join(["%s = %s" % (v[0], v[1]) for v in [("study_id", study_id), ("assay_design", assay_design), ("data_type", data_type), ("study_type", study_type)]])
				log.warn("Skipping assay %s {%s}: %s." % (assay_id, assay_source_path, s))
				map_inc(skipped_assay_count, (study_id, assay_design, data_type, study_type))
			continue

		sample = em.find(sample_id, types.SOURCE_SAMPLE)
		if sample is None:
			log.error("Assay %s references a non-existent sample: %s" % (assay_id, sample_id))
			map_list_add(wrong_assays, study_id, assay_id)
			continue
		
		mf = sample.missing_fields(["id", "basic_sample_details/disease_state", "icdo/topography"])
		if len(mf) > 0:
			sample_id = sample.get("id", "WITHOUT ID")
			doc_path = sample.get("__doc_path", "UNKNOWN")
			sample_source_path = sample.get("source_path", "")
			
			log.error("Sample %s associated with assay %s in study %s missing required fields: %s {%s}" % (sample_id, assay_id, study_id, mf, sample_source_path))
			map_list_add(wrong_samples, study_id, sample_id)
			continue

		sample = sample.transform([
			"id",
			("source_path", "source_path"),
			("disease_state", "basic_sample_details/disease_state"),
			("normal_counterpart", "normal_counterpart_location/topography"),
			("icdo_topography", "icdo/topography"),
			("icdo_morphology", "icdo/morphology") ])
		
		disease_state = sample["disease_state"]
		if disease_state not in disease_state_map:
			log.error("Unknown disease_state '%s' for sample %s {%s}" % (disease_state, sample_id, sample.get("source_path", "")))
			map_list_add(wrong_samples, study_id, sample_id)
			continue

		disease_state = disease_state_map[disease_state]
		if disease_state not in ["tumour", "normal"]:
			continue

		e["disease_state"] = disease_state
		
		e["icdo_topography"] = sample["icdo_topography"]
		e["icdo_morphology"] = sample.get("icdo_morphology", "")
		if "normal_counterpart" in sample:
			e["normal_counterpart"] = sample["normal_counterpart"]

		repo = rs.repository(e["data_file/repo"])
		rel_path = os.path.join(e["data_file/path"], e["data_file/name"])

		if not repo.exists(rel_path):
			log.error("Assay %s in study %s missing data file: [%s]" % (assay_id, study_id, rel_path))
			map_list_add(wrong_assays, study_id, assay_id)
			continue

		key = (study_id, platform_id, sample_id, e["icdo_topography"], e["icdo_morphology"])
		
		eid = None
		duplicated = False
		exists = False
		if data_type == "log_abs_readings":
			if key in absi_dup:
				duplicated = True
			elif key in absi_index:
				eid = absi_index[key][0]
				exists = True
		elif data_type == "log2ratios":
			if key in log2r_source_dup:
				duplicated = True
			elif key in log2r_src_index:
				eid = log2r_src_index[key][0]
				exists = True

		if duplicated:
			log.error("Duplicated key (%s) for assay %s" % (", ".join(key), assay_id))
			map_list_add(wrong_assays, study_id, assay_id)
			continue

		if eid is None:
			eid = str(uuid.uuid4())
		
		e["id"] = eid
		
		if disease_state == "normal":
			if data_type == "log2ratios":
				k = (study_id, platform_id, e.get("normal_counterpart", e["icdo_topography"]))
				map_list_add(log2r_src_units, k, eid)
			elif data_type == "log_abs_readings":
				map_list_add(normal_pools, (study_id, platform_id, e["icdo_topography"]), eid)
			else:
				log.error("Assay %s has an unexpected combination of (disease_state, assay_design, data_type): (%s, %s)" % (assay_id, disease_state, assay_design, data_type))
				map_list_add(wrong_assays, study_id, assay_id)
				continue
		elif disease_state == "tumour":
			k = (study_id, platform_id, e.get("normal_counterpart", e["icdo_topography"]))
			if data_type == "log_abs_readings":
				map_list_add(tumour_units, k, eid)
			elif data_type == "log2ratios":
				map_list_add(log2r_src_units, k, eid)

		processed_studies.add(study_id)
		processed_assays += 1
		map_inc(valid_assay_count, (study_id, platform_id))

		msg = {True : "Overwritting", False : "Writting"}[exists]
		if data_type == "log_abs_readings":
			log.info("%s %s (%s) [%s] ..." % (msg, types.MRNA_ABS_INTENSITY, ", ".join(key), eid))
			em.persist(e, types.MRNA_ABS_INTENSITY)
			absi_port.write(eid)
			absi_dup[key] = eid
		elif data_type == "log2ratios":
			log.info("%s %s (%s) [%s] ..." % (msg, types.MRNA_LOG2R_SOURCE, ", ".join(key), eid))
			em.persist(e, types.MRNA_LOG2R_SOURCE)
			log2r_source_port.write(eid)
			log2r_source_dup[key] = eid

	log.info("Persisting mrna absi tumour units ...")

	for k, v in sorted(tumour_units.items()):
		key = (k[0], k[1], k[2])
		exists = key in absi_tumour_unit_index
		if exists:
			uid = absi_tumour_unit_index[key][0]
		else:
			uid = str(uuid.uuid4())

		u = DataElement(key_sep = "/")
		u["id"] = uid
		u["study_id"] = k[0]
		u["platform_id"] = k[1]
		u["icdo_topography"] = k[2]
		u["size"] = len(v)
		u["mrna_absi_ids"] = u.create_list(v)

		if exists:
			log.debug("\t(%s) ==> %s ..." % (", ".join(k), uid))
		else:
			log.debug("\t(%s) --> %s ..." % (", ".join(k), uid))

		em.persist(u, types.MRNA_ABSI_TUMOUR_UNIT)
		absi_tumour_unit_port.write(uid)

	log.info("Creating indices for mrna normal pools ...")
	normal_pool_index = em.group_ids(
		["study_id", "platform_id", "icdo_topography"],
		types.MRNA_NORMAL_POOL, unique = True)

	log.info("Persisting mrna normal pools ...")

	for k, v in sorted(normal_pools.items()):
		key = (k[0], k[1], k[2])
		exists = key in normal_pool_index
		if exists:
			uid = normal_pool_index[key][0]
		else:
			uid = str(uuid.uuid4())

		u = DataElement(key_sep = "/")
		u["id"] = uid
		u["study_id"] = k[0]
		u["platform_id"] = k[1]
		u["icdo_topography"] = k[2]
		u["size"] = len(v)
		u["mrna_absi_ids"] = u.create_list(v)

		if exists:
			log.debug("\t(%s) ==> %s ..." % (", ".join(k), uid))
		else:
			log.debug("\t(%s) --> %s ..." % (", ".join(k), uid))

		em.persist(u, types.MRNA_NORMAL_POOL)
		normal_pool_port.write(uid)

	sb = ["\n\nProcessed %i assays for %i studies (out of %i):\n\n" % (processed_assays, len(processed_studies), len(study_ids))]
	
	sb += ["%i mrna tumour units:\n\n" % (len(tumour_units))]
	
	for k, v in sorted(tumour_units.items()):
		sb += ["\t(%s)\t%i assays\n" % (", ".join(k), len(v))]

	sb += ["\n%i mrna normal pools:\n\n" % (len(normal_pools))]
	
	for k, v in sorted(normal_pools.items()):
		sb += ["\t(%s)\t%i assays\n" % (", ".join(k), len(v))]
	
	sb += ["\n%i mrna source log2r units:\n\n" % (len(log2r_src_units))]
	
	for k, v in sorted(log2r_src_units.items()):
		sb += ["\t(%s)\t%i assays\n" % (", ".join(k), len(v))]

	sb += ["\nAssay counts by study and platform:\n\n"]
	
	for k, v in sorted(valid_assay_count.items()):
		sb += ["\t%s\t%i assays" % (k, v)]
		if k in wrong_assays:
			sb += ["\t%i failed assays" % len(wrong_assays[k])]
		if k in wrong_samples:
			sb += ["\t%i failed samples" % len(wrong_samples[k])]
		sb += ["\n"]

	log.info("".join(sb))

	if len(skipped_assay_count) > 0:
		log.info("Skipped assays:\n\n%s" % map_count_tostring(skipped_assay_count, indent = 1))

	if len(wrong_assays) > 0:
		log.info("Summary of failed assays:\n\n%s" % map_list_tostring(wrong_assays))

	if len(wrong_samples) > 0:
		log.info("Summary of failed samples:\n\n%s" % map_list_tostring(wrong_samples))

	em.close()

	return 0

if __name__ == "__main__":
	Task(run).start()

