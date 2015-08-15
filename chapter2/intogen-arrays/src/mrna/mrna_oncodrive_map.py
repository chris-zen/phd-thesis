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

import os.path
import os
import uuid
import subprocess
import tempfile

from wok.task import Task
from intogen.io import FileReader, FileWriter
from intogen.utils import skip_file
from intogen.repository import rpath
from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.data.entity import types

def merge_data(row_name, data, map):
	n_index = 0
	pvalue_index = 5 # use 6 for corrected pvalue

	if row_name not in map:
		map[row_name] = data
	else:
		prev_data = map[row_name]
		pvalue = float(data[pvalue_index])
		n = int(data[n_index])
		prev_pvalue = float(prev_data[pvalue_index])
		prev_n = int(prev_data[n_index])
		if (pvalue < prev_pvalue) or \
			(pvalue == prev_pvalue and n > prev_n):
			map[row_name] = data
			return 1

	return 0

def merge(log, input, output, gitools_output):
	"""
	Merge repeated rows by the lowest pvalue, in case the pvalue is the same take the one with greater n
	"""

	f = FileReader(input)
	hdr = f.readline().rstrip().split("\t")
	
	upreg = {}
	downreg = {}

	upreg_count = 0
	downreg_count = 0

	mid_index = 8

	for line in f:
		line = line.rstrip()
		if len(line) == 0:
			continue

		fields = line.split("\t")
		row_name = fields[0]

		upreg_count += merge_data(row_name, fields[1:mid_index], upreg)
		downreg_count += merge_data(row_name, fields[mid_index:], downreg)

	f.close()

	upreg_keys = upreg.keys()
	downreg_keys = downreg.keys()

	log.debug("Total rows: upreg = {}, downreg = {}".format(len(upreg_keys), len(downreg_keys)))
	log.debug("Merged rows: upreg = {}, downreg = {}".format(upreg_count, downreg_count))

	ofile = FileWriter(output)
	ofile.write("\t".join(hdr))
	ofile.write("\n")

	gfile = FileWriter(gitools_output)
	gfile.write("column\trow\t")
	gfile.write("\t".join([x[6:] for x in hdr if x.startswith("upreg_")]))
	gfile.write("\n")

	for row_name in upreg_keys:
		upreg_data = upreg[row_name]
		upreg_data_join = "\t".join(upreg_data)

		downreg_data = downreg[row_name]
		downreg_data_join = "\t".join(downreg_data)

		ofile.write(row_name)
		ofile.write("\t")
		ofile.write(upreg_data_join)
		ofile.write("\t")
		ofile.write(downreg_data_join)
		ofile.write("\n")

		gfile.write("upreg\t")
		gfile.write(row_name)
		gfile.write("\t")
		gfile.write(upreg_data_join)
		gfile.write("\n")
		gfile.write("downreg\t")
		gfile.write(row_name)
		gfile.write("\t")
		gfile.write(downreg_data_join)
		gfile.write("\n")

	ofile.close()
	gfile.close()

	return (upreg_count, downreg_count)

def run(task):

	# Initialization

	task.check_conf(["entities", "repositories", "repositories.data", "repositories.source",
						"bin_paths.python", "bin_paths.matrix_map"])
	conf = task.conf

	log = task.logger()

	task.check_in_ports(["oncodrive_ids"])
	task.check_out_ports(["mapped_oncodrive_ids"])

	oncodrive_port = task.ports["oncodrive_ids"]
	mapped_oncodrive_port = task.ports["mapped_oncodrive_ids"]

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])

	data_repo = rs.repository("data")
	source_repo = rs.repository("source")
	
	overwrite = conf.get("overwrite", False, dtype=bool)

	platform_base_path = "platform"
	vplatform_base_path = "vplatform"

	results_base_path = types.MRNA_ONCODRIVE_GENES.replace(".", "/")

	log.info("Indexing available oncodrive results for genes ...")
	oncodrive_results_index = em.group_ids(
		["study_id", "platform_id", "icdo_topography", "icdo_morphology"],
		types.MRNA_ONCODRIVE_GENES, unique = True)

	for oid in oncodrive_port:
		o = em.find(oid, types.MRNA_ONCODRIVE_PROBES)
		if o is None:
			log.error("{0} not found: {1}".format(types.MRNA_ONCODRIVE_PROBES, oid))
			continue

		study_id = o["study_id"]
		platform_id = o["platform_id"]
		key = (study_id, platform_id, o["icdo_topography"], o["icdo_morphology"])

		if key in oncodrive_results_index:
			mid = oncodrive_results_index[key][0]
			m = em.find(mid, types.MRNA_ONCODRIVE_GENES)
			if m is None:
				log.error("{0} not found: {1}".format(types.MRNA_ONCODRIVE_GENES, mid))
				continue
		else:
			m = o.transform(["study_id", "platform_id",
						"icdo_topography", "icdo_morphology",
						"log2r_tumour_unit_id", ("oncodrive_probes_id", "id")])
			m["id"] = mid = str(uuid.uuid4())

		# mapped oncodrive results

		results_path = rpath.join(results_base_path, mid + ".tsv.gz")
		gitools_results_path = rpath.join(results_base_path, mid + ".tdm.gz")

		if skip_file(overwrite, data_repo, results_path, m.get("results_file")):
			log.warn("Skipping ({0}) [{1}] as it already exists".format(", ".join(key), mid))
			mapped_oncodrive_port.write(mid)
			continue

		log.info("Mapping oncodriver results ({0}) [{1}] ...".format(", ".join(key), oid))

		# determine the mapping file
		map_file = None
		p = em.find(platform_id, types.SOURCE_PLATFORM)
		if p is None:
			log.error("{0} not found: {1}".format(types.SOURCE_PLATFORM, platform_id))
			continue

		platform_id_type = p.get("SO/platform_id_type")
		if platform_id_type is None:
			log.error("Undefined annotation 'SO/platform_id_type' for platform '{0}'.".format(platform_id))
			continue
		elif platform_id_type != "genbank_accession": # affy_accession, custom, ...
			missing = p.missing_fields(["ensg_map", "ensg_map/file"])
			if len(missing) > 0:
				log.error("Missing required fields for platform '{0}': {1}".format(platform_id, ", ".join(missing)))
				continue
			map_file = rpath.join(platform_base_path, p.get("ensg_map/path", ""), p["ensg_map/file"])
			if not source_repo.exists(map_file):
				log.error("Mapping file not found for platform '{0}': {1}".format(platform_id, map_file))
				continue
		elif platform_id_type == "genbank_accession":
			if len(p.missing_fields(["ensg_map", "ensg_map/file"])) > 0:
				map_file = None
			else:
				map_file = rpath.join(platform_base_path, p.get("ensg_map/path", ""), p["ensg_map/file"])
			if map_file is None or not source_repo.exists(map_file):
				vpid = "-".join([platform_id, study_id])
				vp = em.find(vpid, types.SOURCE_VPLATFORM)
				if vp is None:
					log.error("{0} not found: {1}".format(types.SOURCE_VPLATFORM, vpid))
					continue
				missing = vp.missing_fields(["ensg_map", "ensg_map/path", "ensg_map/file"])
				if len(missing) > 0:
					log.error("Missing required fields for vplatform '{0}': {1}".format(vpid, ", ".join(missing)))
					continue
				map_file = rpath.join(vplatform_base_path, vp["ensg_map/path"], vp["ensg_map/file"])
				if not source_repo.exists(map_file):
					log.error("Mapping file not found for vplatform ({0}, {1}): {2}".format(platform_id, study_id, map_file))
					continue
		else:
			log.error("Unknown SO/platform_id_type '{0}' for platform '{1}'.".format(platform_id_type, platform_id))
			continue

		log.debug("Mapping file: {0}".format(map_file))

		m["platform_map_file"] = source_repo.url(map_file)
		
		# oncodrive results file
		repo, repo_path = rs.from_url(o["results_file"])
		local_path = repo.get_local(repo_path)

		# mapped oncodrive results
		m["results_file"] = data_repo.url(results_path)
		results_local_path = data_repo.create_local(results_path)
		gitools_results_local_path = data_repo.create_local(gitools_results_path)

		mapping_path = rpath.join(results_base_path, mid + ".mapping.tsv.gz")
		m["mapping_file"] = data_repo.url(mapping_path)
		mapping_local_path = data_repo.create_local(mapping_path)

		map_results_file = tempfile.mkstemp(prefix = "mrna_oncodrive_map_", suffix=".tsv")[1]

		try:
			# run the mapping tool
			local_map_file = source_repo.get_local(map_file)

			log.debug("Mapping {0} to {1} ...".format(repo_path, map_results_file))

			cmd = " ".join([
				conf["bin_paths.python"], conf["bin_paths.matrix_map"],
				"-o", map_results_file,
				"-i", mapping_local_path,
				local_path,
				local_map_file ])

			log.debug(cmd)

			retcode = subprocess.call(args = cmd, shell = True)

			if retcode != 0:
				raise Exception("There was an error mapping the results")

			# merge repeated ids

			log.debug("Merging {0} to {1} ...".format(map_results_file, results_path))
			log.debug("Gitools file: {0}".format(gitools_results_path))

			upreg_count, downreg_count = merge(log, map_results_file, results_local_path, gitools_results_local_path)
			if upreg_count == 0 and downreg_count == 0:
				log.error("The results of the mapping for ({0}) are empty. This could be because the annotated platform or the mapping file is wrong.".format(", ".join(key)))

			# close local paths
			data_repo.put_local(results_local_path)
			data_repo.put_local(mapping_local_path)
			
		except Exception as e:
			log.exception(e)

			data_repo.close_local(results_local_path)
			data_repo.close_local(mapping_local_path)
			continue

		finally:
			os.remove(map_results_file)
			repo.close_local(local_path)
			source_repo.close_local(local_map_file)

		# save mapped results
		em.persist(m, types.MRNA_ONCODRIVE_GENES)
		mapped_oncodrive_port.write(mid)

	em.close()
	data_repo.close()
	source_repo.close()
	rs.close()

if __name__ == "__main__":
	Task(run).start()
