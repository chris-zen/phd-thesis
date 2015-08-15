#!/usr/bin/env python

"""
Calculate combinations

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
- repositories.data: The path to the repository where data files are written.
- overwrite: (optional) Overwrite already existing files ?. Default = no
- bin_paths.gitools: Path to gitools

* Input:

- combinations: The mrna.combination to process

* Output:

- combination_ids: The ids of the created mrna.combination

* Entities:

- mrna.combination

"""

import sys
import os.path
import os
import subprocess
import shutil
import json
from tempfile import mkdtemp

from wok.task import Task
from wok.element import DataFactory

from intogen import tdm
from intogen.io import FileWriter
from intogen.utils import skip_file
from intogen.repository import rpath
from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.data.entity import types

P_VALUE_FIELD = "right_p_value"

def unflatten_filtered_names(name, id):
	pos = name.find("_")
	if pos == -1:
		return (None, None)
	attr_name = name[pos + 1:]
	if attr_name not in ["n", P_VALUE_FIELD]:
		return (None, None)
	return ("_".join((id, name[0:pos])), attr_name)

def combination(log, conf, rs, c, data_repo, results_path, conditions):

	cid = c["id"]
	ids = c["source/ids"]
	files = c["files"]
	results_url = data_repo.url(results_path)

	try:
		# prepare temporary path and files
		tmp_path = mkdtemp(prefix = "mrna_combination_")
		data_file = os.path.join(tmp_path, "data.tdm")
		columns_file = os.path.join(tmp_path, "columns.gmt")
		tmp_file = os.path.join(tmp_path, "tmp.tdm")
		log.debug("Temporary directory: {}".format(tmp_path))

		# join files to combine in a single TDM file
		log.info("Joining files ...".format(files[0]))
		outpf = FileWriter(data_file)

		log.debug("\t{} ...".format(files[0]))
		repo, path = rs.from_url(files[0])
		local_path = repo.get_local(path)
		ref_hdr = tdm.unflatten(local_path, outpf, row_column = "id",
			column_and_attr_func = lambda name: unflatten_filtered_names(name, ids[0]))

		repo.close_local(path)

		for i in xrange(1, len(files)):
			log.debug("\t{} ...".format(files[i]))
			repo, path = rs.from_url(files[i])
			local_path = repo.get_local(path)
			hdr = tdm.unflatten(local_path, tmp_file, row_column = "id",
				column_and_attr_func = lambda name: unflatten_filtered_names(name, ids[i]))
			tdm.append(outpf, tmp_file, ref_hdr)
			repo.close_local(path)

		outpf.close()

		# prepare conditions columns file in GMT format

		outpf = FileWriter(columns_file)
		for cond in conditions:
			outpf.write(cond)
			outpf.write("\t\t")
			outpf.write("\t".join(["_".join((sid, cond)) for sid in ids]))
			outpf.write("\n")
		outpf.close()

		# run gitools-combination with data.tdm
		log.info("Running gitools combination ...")
		log.debug("\tData: {0}".format(data_file))
		log.debug("\tColumns: {0}".format(columns_file))

		gitools_combination_bin = os.path.join(conf["bin_paths.gitools"], "bin", "gitools-combination")

		cmd = " ".join([ gitools_combination_bin,
			"-N", cid, "-w", tmp_path,
			"-d", data_file,
			"-c", columns_file,
			"-pn", P_VALUE_FIELD,
			"-sn n",
			"-p 1", "-debug" ])

		log.debug(cmd)

		retcode = subprocess.call(args = cmd, shell = True)

		sys.stdout.write("\n")
		sys.stdout.flush()

		if retcode != 0:
			raise Exception("Combination exit code = {0}".format(retcode))

		# flatten results
		log.info("Flattening results into {0} ...".format(results_url))

		try:
			results_local_path = data_repo.create_local(results_path)
			tdm.flatten(os.path.join(tmp_path, cid + "-results.tdm.gz"), results_local_path,
				None, ["N", "z-score", "p-value"])

			data_repo.put_local(results_local_path)
		except:
			data_repo.close_local(results_local_path)

	finally:
		pass#shutil.rmtree(tmp_path)

def run(task):

	# Initialization

	task.check_conf(["entities", "repositories", "repositories.data", "bin_paths.gitools"])
	conf = task.conf

	log = task.logger()

	task.check_in_ports(["combinations"])
	task.check_out_ports(["combination_ids"])

	combinations_port = task.ports["combinations"]
	combination_ids_port = task.ports["combination_ids"]

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])
	data_repo = rs.repository("data")

	overwrite = conf.get("overwrite", False, dtype=bool)

	results_base_path = types.MRNA_COMBINATION.replace(".", "/")

	"""
	log.info("Indexing available combination results ...")
	comb_results_index = em.group_ids(
		["icdo_topography", "icdo_morphology", "id_type"],
		types.MRNA_COMBINATION, unique = True)
	"""

	conditions = ("upreg", "downreg")
	
	for c_str in combinations_port:
		c = DataFactory.from_native(json.loads(c_str), key_sep = "/")
		
		"""
		o = em.find(c, types.MRNA_ONCODRIVE_GENES)
		if o is None:
			log.error("{0} not found: {1}".format(types.MRNA_ONCODRIVE_GENES, c))
			continue

		okey = (o["study_id"], o["platform_id"], o["icdo_topography"], o["icdo_morphology"])
		"""

		cid = c["id"]

		key = (c["icdo_topography"], c["icdo_morphology"], c["id_type"])
		
		log.info("Processing combination for ({0}) [{1}] ...".format(", ".join(key), cid))

		#files = c["files"]
		#if len(files) == 1:
		#	log.info("No combination required, copyed from {0}".format(files[0]))
		#	c["results_file"] = files[0]
		#else:
		results_path = rpath.join(results_base_path, cid + ".tsv.gz")
		results_url = data_repo.url(results_path)

		if skip_file(overwrite, data_repo, results_path, c.get("results_file")):
			log.warn("Skipping {0} ({1}) [{2}] as it already exists".format(types.MRNA_COMBINATION, ", ".join(key), cid))
			combination_ids_port.write(cid)
			continue

		c["results_file"] = results_url

		combination(log, conf, rs, c, data_repo, results_path, conditions)

		# save combination results
		em.persist(c, types.MRNA_COMBINATION)
		combination_ids_port.write(cid)

	em.close()
	data_repo.close()
	rs.close()

if __name__ == "__main__":
	Task(run).start()
