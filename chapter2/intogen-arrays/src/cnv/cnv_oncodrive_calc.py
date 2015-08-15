#!/usr/bin/env python

"""
Calculate oncodrive results for gain and loss

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
- repositories.data: The path to the repository where data files are written.
- overwrite: (optional) Overwrite already existing files ?. Default = no
- bin_paths.gitools: Path to gitools

* Input:

- evt_tumour_unit_ids: The cnv.evt_tumour_unit ids to process

* Output:

- oncodrive_results_ids: The ids of the created cnv.oncodrive

* Entities:

- cnv.evt_tumour_unit, cnv.oncodrive
"""
import os.path

import sys
import os
import uuid
import subprocess
import shutil
from tempfile import mkdtemp

from wok.task import Task
from intogen.io import FileReader, FileWriter
from intogen.matrix import MatrixReader, MatrixWriter
from intogen.utils import skip_file
from intogen.repository import rpath
from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.data.entity import types

def mask_filtering(input_path, output_path, mask):
	mr = MatrixReader(input_path, dtype=int)
	mw = MatrixWriter(output_path, dtype=int)
	mw.write_header(mr.read_header())
	for row in mr:
		values = [1 if (v & mask) != 0 else 0 for v in row.values]
		mw.write(row.name, values)
	mr.close()
	mw.close()

def run_oncodrive(conf, log, oncodrive, cond, matrix_local_path, tmp_path, cmp = None, cmp_value = None):

	prefix = "-".join((oncodrive["id"], cond))
	results_path = os.path.join(tmp_path, prefix + "-results.tdm.gz")
	results_base_path = os.path.dirname(results_path)

	gitools_oncodrive_bin = os.path.join(conf["bin_paths.gitools"], "bin", "gitools-oncodrive")

	cmd = [
		gitools_oncodrive_bin,
		"-N", prefix, "-w", results_base_path,
		"-t binomial", "-p 1",
		"-d", matrix_local_path, "-df cdm"]

	if cmp is not None and cmp_value is not None:
		cmd += ["-b", ",".join((cmp, str(cmp_value)))]

	cmd = " ".join(cmd)

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

def read_data_map(log, gain_results, loss_results):
	dmap = {}

	log.debug("Reading gain data from {} ...".format(gain_results))

	# read gain data
	uf = FileReader(gain_results)
	hdr = read_header(uf)
	count = 0
	for line in uf:
		k, d = read_data(line, hdr, "row", FIELDS)
		dmap[k] = d
		count += 1
	uf.close()

	log.debug("Total gain rows = {0}".format(count))

	log.debug("Reading loss data from {0} ...".format(loss_results))

	# read loss data and join with gain
	df = FileReader(loss_results)
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

	log.debug("Total loss rows = {0}".format(count))

	return dmap

def write_data_map(dmap, path):
	rf = FileWriter(path)
	hdr = ["id"]
	hdr.extend(["_".join(("gain", f.replace("-", "_").lower())) for f in FIELDS])
	hdr.extend(["_".join(("loss", f.replace("-", "_").lower())) for f in FIELDS])
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

task = Task()

@task.main()
def main():

	# Initialization

	task.check_conf(["entities", "repositories", "bin_paths.gitools"])
	conf = task.conf

	log = task.logger()

	evt_tumour_unit_port, oncodrive_results_port = \
		task.ports("evt_tumour_unit_ids", "oncodrive_results_ids")

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])
	data_repo = rs.repository("data")

	overwrite = conf.get("overwrite", False, dtype=bool)

	# Run

	log.info("Indexing available {} ...".format(types.CNV_ONCODRIVE_GENES))
	oncodrive_results_index = em.group_ids(
		["study_id", "platform_id", "icdo_topography", "icdo_morphology"],
		types.CNV_ONCODRIVE_GENES, unique = True)

	results_base_path = types.CNV_ONCODRIVE_GENES.replace(".", "/")

	for uid in evt_tumour_unit_port:
		u = em.find(uid, types.CNV_EVENTS_TUMOUR_UNIT)
		if u is None:
			log.error("{} not found: {}".format(types.CNV_EVENTS_TUMOUR_UNIT, uid))
			continue

		key = (u["study_id"], u["platform_id"], u["icdo_topography"], u["icdo_morphology"])
		if key in oncodrive_results_index:
			eid = oncodrive_results_index[key][0]
			e = em.find(eid, types.CNV_ONCODRIVE_GENES)
			if e is None:
				log.error("{} not found: {}".format(types.CNV_ONCODRIVE_GENES, eid))
				continue
		else:
			e = u.transform(["study_id", "platform_id", "icdo_topography", "icdo_morphology"])
			eid = e["id"] = str(uuid.uuid4())

		# create oncodrive results entity
		e["evt_tumour_unit_id"] = uid

		results_path = rpath.join(results_base_path, eid + ".tsv.gz")

		if skip_file(overwrite, data_repo, results_path, e.get("results_file")):
			log.warn("Skipping ({}) [{}] as it already exists".format(", ".join(key), eid))
			oncodrive_results_port.write(eid)
			continue

		e["results_file"] = data_repo.url(results_path)
		
		# data matrix for oncodrive calculation
		matrix_repo, matrix_path = rs.from_url(u["data_file"])

		# Gain & Loss

		log.info("Calculating Oncodrive results for {} ({}) [{}] ...".format(types.CNV_EVENTS_TUMOUR_UNIT, ", ".join(key), uid))
		log.debug("{} id is {}".format(types.CNV_ONCODRIVE_GENES, eid))

		tmp_path = mkdtemp(prefix = "cnv_oncodrive_calc_")
		log.debug("Temporary directory: {}".format(tmp_path))
		tmp_file = os.path.join(tmp_path, "filtered_data.tsv")

		matrix_local_path = matrix_repo.get_local(matrix_path)
		log.debug("Matrix path: {}".format(matrix_path))

		try:
			try:
				log.info("Calculating Gain ...")
				log.debug("Bit mask filtering (01) {} to {} ...".format(matrix_local_path, tmp_file))
				mask_filtering(matrix_local_path, tmp_file, 1)
				gain_results = run_oncodrive(
					conf, log, e, "gain", tmp_file, tmp_path)
			except:
				log.error("Oncodrive calculation for evt tumour unit ({}) [{}] for gain failed".format(",".join(key), uid))
				matrix_repo.close_local(matrix_local_path)
				raise

			try:
				log.info("Calculating Loss ...")
				log.debug("Bit mask filtering (10) {} to {} ...".format(matrix_local_path, tmp_file))
				mask_filtering(matrix_local_path, tmp_file, 2)
				loss_results = run_oncodrive(
					conf, log, e, "loss", tmp_file, tmp_path)
			except:
				log.error("Oncodrive calculation for evt tumour unit ({}) [{}] for downreg failed".format(",".join(key), uid))
				matrix_repo.close_local(matrix_local_path)
				raise

			# Join gain & loss results

			log.info("Joining upreg & downreg results into memory ...")

			# the join is done in memory with a map
			dmap = read_data_map(log, gain_results, loss_results)

			log.info("Writting joined data to {} ...".format(results_path))

			results_local_path = data_repo.create_local(results_path)

			write_data_map(dmap, results_local_path)

		finally:
			matrix_repo.close_local(matrix_local_path)
			matrix_repo.close()

			if os.path.exists(tmp_path):
				log.debug("Removing temporary directory {} ...".format(tmp_path))
				shutil.rmtree(tmp_path)

		data_repo.put_local(results_local_path)

		em.persist(e, types.CNV_ONCODRIVE_GENES)
		oncodrive_results_port.write(eid)
	
	em.close()
	data_repo.close()
	rs.close()
	
task.start()
