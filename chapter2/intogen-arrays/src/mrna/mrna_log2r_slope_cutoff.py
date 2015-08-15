#!/usr/bin/env python

import os
import uuid
import subprocess

from wok.task import Task
from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.data.entity import types

"""
Calculate a slope based cutoff for the mrna.log2r_tumour_unit for upregulation and downregulation

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
- repositories.data: (optional) The path to the repository where data files are written. Default value = work.path
- overwrite: (optional) Overwrite already existing files ?. Default = no
- bin_paths.R: Path to R
- mrna.log2r_slope_cutoff.slope: (optional) The slope to use for calculating the cutoff. Default -0.05

* Input:

- log2r_tumour_unit_ids: The mrna.log2r_tumour_unit ids to process

* Output:

- log2r_tumour_unit_ids: The mrna.log2r_tumour_unit ids processed
- log2r_cutoff_ids: The ids of the creted mrna.log2r_cutoff

* Entities:

- mrna.log2r_tumour_unit, mrna.log2r_cutoff

"""

def calc_cutoff(conf, log, log2r_unit_id, matrix_repo, matrix_path, data_repo, cutoff_path, cond, slope):
	prefix = "%s.%s" % (log2r_unit_id, cond)
	cutoff_file_name = prefix + ".cutoff"
	cutoff_repo_path = os.path.join(cutoff_path, cutoff_file_name)
	plot_file_name = prefix + ".ps"
	plot_repo_path = os.path.join(cutoff_path, plot_file_name)

	matrix_local_path = matrix_repo.get_local(matrix_path)
	cutoff_local_file = data_repo.create_local(cutoff_repo_path)
	plot_local_file = data_repo.create_local(plot_repo_path)

	script = "%s/mrna_log2r_slope_cutoff.R" % conf["wok.__flow.path"] #TODO avoid using wok.__flow.path

	args = [matrix_local_path, cond, slope, cutoff_local_file, plot_local_file]
	cmd = "%s --vanilla --slave -f %s --args %s" % (conf["bin_paths.R"], script, " ".join(args))
	log.debug(cmd)

	retcode = subprocess.call(args = cmd, shell = True)

	if retcode != 0:
		raise Exception("R script failed")

	if not os.path.exists(cutoff_local_file):
		raise Exception("Cutoff file not found: %s" % cutoff_local_file)

	f = open(cutoff_local_file, "r")
	cutoff = float(f.readline().rstrip())
	f.close()

	matrix_repo.close_local(matrix_local_path)
	data_repo.put_local(cutoff_local_file)
	data_repo.put_local(plot_local_file)

	return (cutoff, cutoff_local_file, plot_repo_path)

def run(task):

	# Initialization

	task.check_conf(["entities", "repositories", "bin_paths.R"])
	conf = task.conf

	log = task.logger()

	task.check_in_ports(["log2r_tumour_unit_ids"])
	task.check_out_ports(["processed_log2r_tumour_unit_ids"])

	log2r_tumour_unit_port = task.ports["log2r_tumour_unit_ids"]
	processed_log2r_tumour_unit_port = task.ports["processed_log2r_tumour_unit_ids"]
	
	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])
	data_repo = rs.repository("data")

	overwrite = conf.get("overwrite", False, dtype=bool)

	# Run

	log.info("Indexing available mrna log2r cutoffs ...")
	log2r_cutoff_index = em.group_ids(
		["study_id", "platform_id", "icdo_topography", "icdo_morphology"],
		types.MRNA_LOG2R_CUTOFF, unique = True)

	cutoff_path = types.MRNA_LOG2R_CUTOFF.replace(".", "/")

	for log2r_unit_id in log2r_tumour_unit_port:
		u = em.find(log2r_unit_id, types.MRNA_LOG2R_TUMOUR_UNIT)
		if u is None:
			log.error("%s not found: %s" % (types.MRNA_LOG2R_TUMOUR_UNIT, log2r_unit_id))
			continue

		key = (u["study_id"], u["platform_id"], u["icdo_topography"], u["icdo_morphology"])
		if key in log2r_cutoff_index:
			eid = log2r_cutoff_index[key][0]
			e = em.find(eid, types.MRNA_LOG2R_CUTOFF)
			if ("upreg/cutoff" in e) and ("upreg/cutoff" in e) and not overwrite:
				log.warn("Skipping (%s) [%s] as it already exists" % (", ".join(key), eid))
				processed_log2r_tumour_unit_port.write(log2r_unit_id)
				continue
		else:
			e = u.transform(["study_id", "platform_id", "icdo_topography", "icdo_morphology"])
			eid = e["id"] = str(uuid.uuid4())

		log.info("Calculating cutoffs for {} ({}) [{}] ...".format(types.MRNA_LOG2R_TUMOUR_UNIT, ", ".join(key), log2r_unit_id))
		log.debug("{} id is {}".format(types.MRNA_LOG2R_CUTOFF, eid))

		file_repo = u["data_file/repo"]
		matrix_repo = rs.repository(file_repo)

		file_path = u["data_file/path"]
		file_name = u["data_file/file"]
		matrix_path = os.path.join(file_path, file_name)

		if "mrna.log2r_slope_cutoff.slope" in conf:
			slope = conf["mrna.log2r_slope_cutoff.slope"]
		else:
			slope = str(-0.05)

		log.debug("slope = {}".format(slope))

		# Upregulation

		log.info("Upregulation ...")

		try:
			cutoff, cutoff_file, plot_file = calc_cutoff(
				conf, log, log2r_unit_id, matrix_repo, matrix_path, data_repo, cutoff_path, "upreg", slope)
		except Exception as e:
			log.error("Upreg cutoff calculation for {} ({}) [{}] failed".format(types.MRNA_LOG2R_TUMOUR_UNIT, ",".join(key), log2r_unit_id))
			log.exception(e)
			return -1

		log.debug("Upregulation cutoff = {}".format(cutoff))

		e["upreg/cutoff"] = cutoff

		e["upreg/plot_file"] = pf = e.create_element()
		pf["repo"] = data_repo.name()
		pf["path"] = os.path.dirname(plot_file)
		pf["file"] = os.path.basename(plot_file)

		# Downregulation

		log.info("Downregulation ...")

		try:
			cutoff, cutoff_file, plot_file = calc_cutoff(
				conf, log, log2r_unit_id, matrix_repo, matrix_path, data_repo, cutoff_path, "downreg", slope)
		except Exception as e:
			log.error("Downreg cutoff calculation for {} ({}) [{}] failed".format(types.MRNA_LOG2R_TUMOUR_UNIT, ",".join(key), log2r_unit_id))
			log.exception(e)
			return -1

		log.debug("Downregulation cutoff = {}".format(cutoff))

		e["downreg/cutoff"] = cutoff

		e["downreg/plot_file"] = pf = e.create_element()
		pf["repo"] = data_repo.name()
		pf["path"] = os.path.dirname(plot_file)
		pf["file"] = os.path.basename(plot_file)

		em.persist(e, types.MRNA_LOG2R_CUTOFF)
		processed_log2r_tumour_unit_port.write(log2r_unit_id)
		
	em.close()
	
	data_repo.close()

if __name__ == "__main__":
	Task(run).start()
