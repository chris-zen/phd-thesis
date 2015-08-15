#!/usr/bin/env python

"""
Calculate oncodrive results for upregulation and downregulation using the cutoffs calculated previously

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
- repositories.data: (optional) The path to the repository where data files are written. Default value = work.path
- overwrite: (optional) Overwrite already existing files ?. Default = no
- bin_paths.gitools: Path to gitools

* Input:

- log2r_tumour_unit_ids: The mrna.log2r_tumour_unit ids to process

* Output:

- oncodrive_results_ids: The ids of the created mrna.oncodrive_probes

* Entities:

- mrna.log2r_tumour_unit, mrna.log2r_cutoff, mrna.oncodrive_probes

"""

import sys
import os
import uuid
import subprocess

from wok.task import Task
from intogen.io import FileReader, FileWriter
from intogen.utils import skip_file
from intogen.repository import rpath
from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.data.entity import types

def run_oncodrive(conf, log, oncodrive, cond, matrix_local_path, cmp, cutoff, tmp_path):

	prefix = "-".join((oncodrive["id"], cond))
	results_path = os.path.join(tmp_path, prefix + "-results.tdm.gz")
	results_base_path = os.path.dirname(results_path)

	gitools_oncodrive_bin = os.path.join(conf["bin_paths.gitools"], "bin", "gitools-oncodrive")

	cmd = " ".join([
		gitools_oncodrive_bin,
		"-N", prefix, "-w", results_base_path,
		"-t binomial", "-p 1",
		"-d", matrix_local_path, "-df cdm",
		"-b", ",".join((cmp, str(cutoff)))])

	log.debug(cmd)

	retcode = subprocess.call(args = cmd, shell = True)
	sys.stdout.write("\n")
	sys.stdout.flush()

	if retcode != 0:
		raise Exception("Oncodrive exit code = %i" % retcode)

	return results_path

def read_header(f):
	hdr = {}
	line = f.readline().lstrip()
	while len(line) > 0 and line[0] == '#':
		line = f.readline().lstrip()

	fields = line.rstrip().split("\t")
	for index, h in enumerate(fields):
		if len(h) > 2 and h[0] == '"' and h[-1] == '"':
			h = h[1:-1]
		hdr[h] = index

	return hdr

def read_data(line, hdr, key_field, fields):
	data = []
	l = line.rstrip().split("\t")

	index = hdr[key_field]
	d = l[index]
	if len(d) > 2 and d[0] == '"' and d[-1] == '"':
		d = d[1:-1]
	key = d

	for field in fields:
		index = hdr[field]
		d = l[index]
		if len(d) > 2 and d[0] == '"' and d[-1] == '"':
			d = d[1:-1]
		data += [d]

	return key, data

# Fields to retrieve from oncodrive results
FIELDS = [
	"N", "observed",
	"expected-mean", "expected-stdev", "probability",
	"right-p-value", "corrected-right-p-value"]

def read_data_map(log, upreg_results, downreg_results):
	dmap = {}

	log.debug("Reading upreg data from {0} ...".format(upreg_results))

	# read upreg data
	uf = FileReader(upreg_results)
	hdr = read_header(uf)
	count = 0
	for line in uf:
		k, d = read_data(line, hdr, "row", FIELDS)
		dmap[k] = d
		count += 1
	uf.close()

	log.debug("Total upreg rows = {0}".format(count))

	log.debug("Reading downreg data from {0} ...".format(downreg_results))

	# read downreg data and join with upreg
	df = FileReader(downreg_results)
	hdr = read_header(df)
	count = 0
	for line in df:
		k, d = read_data(line, hdr, "row", FIELDS)
		if k not in dmap:
			data = ["-"] * len(FIELDS)
		else:
			data = dmap[k]
		data += d
		dmap[k] = data
		count += 1

	log.debug("Total downreg rows = {0}".format(count))

	return dmap

def write_data_map(dmap, path):
	rf = FileWriter(path)
	hdr = ["id"]
	hdr.extend(["_".join(("upreg", f.replace("-", "_").lower())) for f in FIELDS])
	hdr.extend(["_".join(("downreg", f.replace("-", "_").lower())) for f in FIELDS])
	rf.write("\t".join(hdr) + "\n")
	for row, values in dmap.iteritems():
		rf.write(row)
		for v in values:
			rf.write("\t")
			rf.write(v)
		if len(values) == len(FIELDS):
			rf.write("\t".join(["-"] * len(FIELDS)))
		rf.write("\n")
	rf.close()

def run(task):

	# Initialization

	task.check_conf(["entities", "repositories", "bin_paths.gitools"])
	conf = task.conf

	log = task.logger()

	task.check_in_ports(["log2r_tumour_unit_ids"])
	task.check_out_ports(["oncodrive_results_ids"])

	log2r_tumour_unit_port = task.ports["log2r_tumour_unit_ids"]
	oncodrive_results_port = task.ports["oncodrive_results_ids"]

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])
	data_repo = rs.repository("data")

	overwrite = conf.get("overwrite", False, dtype=bool)

	# Run

	log.info("Indexing available oncodrive results for probes ...")
	oncodrive_results_index = em.group_ids(
		["study_id", "platform_id", "icdo_topography", "icdo_morphology"],
		types.MRNA_ONCODRIVE_PROBES, unique = True)

	log.info("Indexing available mrna log2r cutoffs ...")
	log2r_cutoff_index = em.group_ids(
		["study_id", "platform_id", "icdo_topography", "icdo_morphology"],
		types.MRNA_LOG2R_CUTOFF, unique = True)

	results_base_path = types.MRNA_ONCODRIVE_PROBES.replace(".", "/")

	for log2r_unit_id in log2r_tumour_unit_port:
		u = em.find(log2r_unit_id, types.MRNA_LOG2R_TUMOUR_UNIT)
		if u is None:
			log.error("{} not found: {}".format(types.MRNA_LOG2R_TUMOUR_UNIT, log2r_unit_id))
			continue

		key = (u["study_id"], u["platform_id"], u["icdo_topography"], u["icdo_morphology"])
		if key in oncodrive_results_index:
			eid = oncodrive_results_index[key][0]
			e = em.find(eid, types.MRNA_ONCODRIVE_PROBES)
			if e is None:
				log.error("{} not found: {}".format(types.MRNA_ONCODRIVE_PROBES, eid))
				continue
		else:
			e = u.transform(["study_id", "platform_id", "icdo_topography", "icdo_morphology"])
			eid = e["id"] = str(uuid.uuid4())

		log.info("Calculating Oncodrive results for {} ({}) [{}] ...".format(types.MRNA_LOG2R_TUMOUR_UNIT, ", ".join(key), log2r_unit_id))
		log.debug("{} id is {}".format(types.MRNA_ONCODRIVE_PROBES, eid))

		# create oncodrive results entity
		e["log2r_tumour_unit_id"] = log2r_unit_id

		results_path = rpath.join(results_base_path, eid + ".tsv.gz")

		if skip_file(overwrite, data_repo, results_path, e.get("results_file")):
			log.warn("Skipping ({}) [{}] as it already exists".format(", ".join(key), eid))
			oncodrive_results_port.write(eid)
			continue

		e["results_file"] = data_repo.url(results_path)
		
		# data matrix for oncodrive calculation
		file_repo = u["data_file/repo"]
		matrix_repo = rs.repository(file_repo)

		file_path = u["data_file/path"]
		file_name = u["data_file/file"]
		matrix_path = os.path.join(file_path, file_name)

		# Load calculated cutoff

		log.info("Loading mrna cutoff for key ({}) ...".format(", ".join(key)))

		if key not in log2r_cutoff_index:
			log.error("mrna log2r cuttof not found for key ({})".format(", ".join(key)))
			matrix_repo.close()
			continue

		cutoff_id = log2r_cutoff_index[key][0]
		cutoff = em.find(cutoff_id, types.MRNA_LOG2R_CUTOFF)
		if cutoff is None:
			log.error("mrna log2r cuttof for key ({}) [{}] couldn't be loaded".format(", ".join(key), cutoff_id))
			matrix_repo.close()
			continue

		log.debug("{} id is {}".format(types.MRNA_LOG2R_CUTOFF, cutoff_id))

		# Upregulation & downregulation

		try:
			from tempfile import mkdtemp
			tmp_path = mkdtemp(prefix = "mrna_oncodrive_calc_")
			log.debug("Temporary directory: {}".format(tmp_path))

			matrix_local_path = matrix_repo.get_local(matrix_path)
			log.debug("Matrix path: {}".format(matrix_path))

			try:
				log.info("Calculating Upregulation with cutoff {} ...".format(cutoff["upreg/cutoff"]))
				upreg_results = run_oncodrive(
					conf, log, e, "upreg", matrix_local_path,
					"gt", cutoff["upreg/cutoff"], tmp_path)
			except:
				log.error("Oncodrive calculation for upreg failed")
				matrix_repo.close_local(matrix_local_path)
				raise

			try:
				log.info("Calculating Downregulation with cutoff {} ...".format(cutoff["downreg/cutoff"]))
				downreg_results = run_oncodrive(
					conf, log, e, "downreg", matrix_local_path,
					"lt", cutoff["downreg/cutoff"], tmp_path)
			except:
				log.error("Oncodrive calculation for downreg failed")
				matrix_repo.close_local(matrix_local_path)
				raise

			# Join upreg & downreg results

			log.info("Joining upreg & downreg results into memory ...")

			# the join is done in memory with a map
			dmap = read_data_map(log, upreg_results, downreg_results)

			log.info("Writting joined results to {} ...".format(results_path))

			results_local_path = data_repo.create_local(results_path)

			write_data_map(dmap, results_local_path)

		finally:
			matrix_repo.close_local(matrix_local_path)
			matrix_repo.close()

			if os.path.exists(tmp_path):
				log.debug("Removing temporary directory {} ...".format(tmp_path))
				import shutil
				shutil.rmtree(tmp_path)

		data_repo.put_local(results_local_path)

		em.persist(e, types.MRNA_ONCODRIVE_PROBES)
		oncodrive_results_port.write(eid)
	
	em.close()
	data_repo.close()
	rs.close()
	
if __name__ == "__main__":
	Task(run).start()
