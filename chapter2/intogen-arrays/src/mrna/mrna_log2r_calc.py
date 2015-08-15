#!/usr/bin/env python

"""
Calculate log2 ratios for mrna abs intensity tumour assays

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
- repositories.assay: The path to the repository where the assay data files are
- repositories.data: (optional) The path to the repository where data files are written. Default value = work.path
- overwrite: (optional) Overwrite already existing entities ?. Default = no

* Input:

- absi_tumour_unit_ids: list of mrna absi tumour unit ids (mrna.absi_tumour_unit) to process.

* Output:

- log2r_ids: list of log2r assay ids (mrna.log2r) to process

* Entities:

- mrna.log2r
"""

import os
import numpy
import uuid
from copy import deepcopy

from wok.task import Task
from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.data.entity import types
from intogen.matrix import MatrixReader, MatrixWriter

def iter_tumour_absi(conf, em, absi_tumour_unit_ids, log):
	#prev_ids = set()
	for unit in em.iter_all(types.MRNA_ABSI_TUMOUR_UNIT, absi_tumour_unit_ids):
		#study_id = unit["study_id"]
		#platform_id = unit["platform_id"]
		for absi_id in unit["mrna_absi_ids"]:
			log.debug("Reading abs intensity assay '%s' ..." % absi_id)
			absi = em.find(absi_id, types.MRNA_ABS_INTENSITY)

			if absi is None:
				log.error("Abs intensity assay '%s' not found by the entity manager !" % absi_id)
				continue

			if absi["disease_state"] != "tumour":
				log.warn("Unexpected disease state '%s' for abs intensity assay '%s'" % (absi["disease_state"], absi_id))
				continue

			mf = absi.missing_fields(["study_id", "platform_id", "icdo_topography"])
			if len(mf) > 0:
				log.error("Tumour assay %s missing required fields: %s {%s}" % (absi_id, mf, unit.get("__doc_path", "")))
				continue

			#prev_ids.add(absi_id)
			yield absi

def log2r_exists(rs, absi):
	mf = absi.missing_fields(["log2r_id", "log2r_data_file"])
	if len(mf) > 0:
		return False

	file_repo = absi["log2r_data_file/repo"]
	repo = rs.repository(file_repo)

	file_path = absi["log2r_data_file/path"]
	file_name = absi["log2r_data_file/name"]	
	rpath = os.path.join(file_path, file_name)
		
	return repo.exists(rpath)
	
def read_pool_data(conf, rs, pool, log):
	pool_data = {}
	
	mf = pool.missing_fields(["study_id", "platform_id", "icdo_topography", "data_file/repo", "data_file/path", "data_file/name"])
	if len(mf) > 0:
		log.error("Normal pool %s has missing fields: %s" % (pool["id"], ", ".join(mf)))
		return None

	key = "(%s, %s, %s)" % (pool["study_id"], pool["platform_id"], pool["icdo_topography"])
	
	log.info("Reading normal pool %s %s ..." % (key, pool["id"]))

	file_repo = pool["data_file/repo"]
	repo = rs.repository(file_repo)

	file_path = pool["data_file/path"]
	file_name = pool["data_file/name"]
	rpath = os.path.join(file_path, file_name)
	
	log.debug("Reading normal pool data from %s ..." % (rpath))
	
	mr = MatrixReader(repo.open_reader(rpath))
	header = mr.read_header()
	if len(header.columns) != 2:
		log.error("Unexpected number of columns: %i" % len(header.columns))
		mr.close()
		return None

	for row in mr:
		pool_data[row.name] = row.values[0]

	mr.close()
	
	return pool_data

def run(task):
	
	# Initialization

	task.check_conf(["entities", "repositories", "repositories.assay"])
	conf = task.conf

	log = task.logger()

	task.check_in_ports(["absi_tumour_unit_ids"])
	task.check_out_ports(["log2r_ids"])

	absi_tumour_unit_port = task.ports["absi_tumour_unit_ids"]
	log2r_port = task.ports["log2r_ids"]

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])
	data_repo = rs.repository("data")

	overwrite = conf.get("overwrite", False, dtype=bool)
	
	# Run
	
	# Index normal pools by study, platform, topography
	log.debug("Indexing normal pools by study, platform and topography ...")
	pools_index = em.group_ids(
		["study_id", "platform_id", "icdo_topography"],
		types.MRNA_NORMAL_POOL, unique = True)

	# Index log2r assays by absi_id
	log.debug("Indexing log2r assays by absi assay ...")
	log2r_index = em.group_ids(
		["absi_id"],
		types.MRNA_LOG2R, unique = True)

	absi_tumour_unit_ids = absi_tumour_unit_port.read_all()
	
	log.info("Processing %i mrna absi tumour units ..." % len(absi_tumour_unit_ids))
	#log.debug("[%s]" % (", ".join(absi_tumour_unit_ids)))

	# For each abs intensity assay
	pool = None
	pool_data = {}
	for absi in iter_tumour_absi(conf, em, absi_tumour_unit_ids, log):

		absi_id = absi["id"]

		rpath = os.path.join(absi["data_file/path"], absi["data_file/name"])
		
		icdo_topography = absi["icdo_topography"]
		normal_counterpart = absi.get("normal_counterpart", icdo_topography)
		if icdo_topography != normal_counterpart:
			keystr = "(%s, %s, %s --> %s)" % (absi["study_id"], absi["platform_id"], icdo_topography, normal_counterpart)
		else:
			keystr = "(%s, %s, %s)" % (absi["study_id"], absi["platform_id"], icdo_topography)

		exists = (absi_id,) in log2r_index
		if exists:
			log2r_id = log2r_index[(absi_id,)][0]
		else:
			log2r_id = str(uuid.uuid4())

		data_file_path = types.MRNA_LOG2R.replace(".", "/")
		data_file_name = log2r_id + ".tsv.gz"
		dst_path = os.path.join(data_file_path, data_file_name)

		if not overwrite and exists and data_repo.exists(dst_path):
			log.debug("Skipping calculation of log2r for tumour assay %s %s as it is already calculated" % (keystr, absi_id))
			log2r_port.write(log2r_id)
			continue

		log.info("Processing tumour assay %s %s from %s ..." % (keystr, absi_id, rpath))

		repo = rs.repository(absi["data_file/repo"])
		if not repo.exists(rpath):
			log.error("File not found: %s" % rpath)
			continue

		# Get normal counterpart data
		if pool is None \
			or absi["study_id"] != pool["study_id"] \
			or absi["platform_id"] != pool["platform_id"] \
			or normal_counterpart != pool["icdo_topography"]:

			pool_key = (absi["study_id"], absi["platform_id"], normal_counterpart)
			if pool_key not in pools_index:
				log.error("Normal pool not found for tumour assay (%s) %s {%s}" % (", ".join(pool_key), absi_id, absi.get("source_path", "")))
				continue

			pool_id = pools_index[pool_key][0]
			pool = em.find(pool_id, types.MRNA_NORMAL_POOL)
			if pool is None:
				log.error("Normal pool %s not found by the entity manager !" % pool_id)
				continue
			
			pool_data = read_pool_data(conf, rs, pool, log)
			if pool_data is None:
				pool = None
				continue

		log.info("Using normal pool ({}) [{}]".format(", ".join(pool_key), pool_id))

		# Calculate log2 ratios
		mr = MatrixReader(repo.open_reader(rpath))
		header = mr.read_header()
		if len(header.columns) != 2:
			log.error("Unexpected number of columns: %i" % len(header.columns))
			mr.close()
			continue

		warn_count = {
			"id_not_in_pool" : 0,
			"value_is_nan" : 0,
			"pool_value_is_nan" : 0,
			"value_is_inf" : 0,
			"pool_value_is_inf" : 0}

		data = {}
		for row in mr:
			if row.name in data:
				log.error("Skipping tumour assay, duplicated row %s at file %s" % (row.name, rpath))
				break

			value = row.values[0]

			value_is_nan = numpy.isnan(value)

			if value_is_nan:
				warn_count["value_is_nan"] += 1
			elif numpy.isinf(value):
				warn_count["value_is_inf"] += 1

			if row.name not in pool_data:
				pool_value = value = numpy.nan
				warn_count["id_not_in_pool"] += 1
			else:
				pool_value = pool_data[row.name]

			pool_value_is_nan = numpy.isnan(pool_value)
			if pool_value_is_nan:
				warn_count["pool_value_is_nan"] += 1
			elif numpy.isinf(pool_value):
				warn_count["pool_value_is_inf"] += 1

			if not value_is_nan and not pool_value_is_nan: # and value != 0.0 and pool_value != 0.0:
				log2r = value - pool_value
			else:
				log2r = numpy.nan

			if not numpy.isinf(log2r):
				data[row.name] = log2r
			#else:
			#	log.warn("row = %s, log2r = %f, value = %f, pool_value = %f" % (row.name, log2r, value, pool_value))

		mr.close()
		
		sb = ["{0}={1}".format(k, v) for k, v in warn_count.items() if v > 0]
		if len(sb) > 0:
			log.warn(", ".join(sb))

		# Save log2 ratios data and assay
		log2r = deepcopy(absi)

		log2r["id"] = log2r_id
		log2r["absi_id"] = absi_id
		log2r["normal_pool_id"] = pool["id"]

		log2r["data_file/repo"] = data_repo.name()
		log2r["data_file/path"] = data_file_path
		log2r["data_file/name"] = data_file_name

		msg = {True : "Overwritting", False : "Writting"}[exists]
		log.debug("%s log2 ratio data to %s ..." % (msg, dst_path))

		mw = MatrixWriter(data_repo.open_writer(dst_path))
		mw.write_header(["id", "value"])
		for name, value in sorted(data.items()):
			mw.write(name, [value])
		mw.close()

		em.persist(log2r, types.MRNA_LOG2R)
		log2r_port.write(log2r_id)

	em.close()
	es.close()

	data_repo.close()
	rs.close()

if __name__ == "__main__":
	Task(run).start()
