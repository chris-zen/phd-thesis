#!/usr/bin/env python

"""
Join mrna.log2r assay data files in one matrix with one column per mrna.log2r

* Configuration parameters:

- The ones required by intogen.data.entity.EntityManagerFactory
- repositories.data: The path to the repository where data files are written.
- overwrite: (optional) Overwrite already existing files ?. Default = no
- python_bin: (optional) Path to python binary
- bin_paths.matrix_join: Path to bg-scripts/matrix/matrix-join.py script

* Input:

- log2r_tumour_unit_ids: The mrna.log2r_tumour_unit ids to process

* Output:

- joined_log2r_tumour_unit_ids: The ids of the mrna.log2r_tumour_unit's updated

* Entities:

- mrna.log2r_tumour_unit

"""

import os
import os.path
import subprocess

from wok.task import Task
from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer
from intogen.data.entity import types


def run(task):

	# Initialization

	task.check_conf(["entities", "repositories", "bin_paths.matrix_join", "bin_paths.python"])
	conf = task.conf

	log = task.logger()

	task.check_in_ports(["log2r_tumour_unit_ids"])
	task.check_out_ports(["joined_log2r_tumour_unit_ids"])

	log2r_tumour_unit_port = task.ports["log2r_tumour_unit_ids"]
	joined_log2r_tumour_unit_port = task.ports["joined_log2r_tumour_unit_ids"]

	python_bin = conf["bin_paths.python"]

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])
	data_repo = rs.repository("data")

	overwrite = conf.get("overwrite", False, dtype=bool)

	# Run

	unit_base_path = types.MRNA_LOG2R_TUMOUR_UNIT.replace(".", "/")
	
	for log2r_unit_id in log2r_tumour_unit_port:
		u = em.find(log2r_unit_id, types.MRNA_LOG2R_TUMOUR_UNIT)
		if u is None:
			log.error("%s not found: %s" % (types.MRNA_LOG2R_TUMOUR_UNIT, log2r_unit_id))
			continue
		
		uid = u["id"]
		study_id = u["study_id"]
		platform_id = u["platform_id"]
		icdo_topography = u["icdo_topography"]
		icdo_morphology = u["icdo_morphology"]
		key = (study_id, platform_id, icdo_topography, icdo_morphology)

		log.info("Joining columns for {} ({}) [{}] ...".format(types.MRNA_LOG2R_TUMOUR_UNIT, ", ".join(key), log2r_unit_id))

		if "mrna_log2r_ids" not in u:
			log.warn("Discarding empty unit (%s) [%s]" % (", ".join(key), log2r_unit_id))
			continue

		unit_repo = data_repo

		if "data_file" in u:
			unit_repo = rs.repository(u["data_file/repo"])
			unit_repo_path = os.path.join(u["data_file/path"], u["data_file/file"])
			exists = unit_repo is not None and unit_repo.exists(unit_repo_path)
		else:
			unit_repo_path = os.path.join(unit_base_path, log2r_unit_id + ".tsv.gz")
			exists = False

		if exists and not overwrite:
			log.warn("Skipping log2r tumour unit data join (%s) [%s] as it already exists in %s" % (", ".join(key), log2r_unit_id, unit_repo_path))
			joined_log2r_tumour_unit_port.write(uid)
			continue

		valid = True
		repos = []
		files = []
		for log2r_id in u["mrna_log2r_ids"]:
			e = em.find(log2r_id, types.MRNA_LOG2R)
			if e is None:
				log.error("log2r assay '%s' not found" % log2r_id)
				valid = False
				break

			repo = rs.repository(e["data_file/repo"])
			repo_path = os.path.join(e["data_file/path"], e["data_file/name"])

			if repo is None or not repo.exists(repo_path):
				log.error("File not found: %s" % repo_path)
				valid = False
				break

			repos += [repo]
			files += [repo.get_local(repo_path)]

		if not valid:
			log.info("Skipping log2r tumour unit (%s) [%s] as there were errors" % (", ".join(key), log2r_unit_id))
			continue

		if exists:
			unit_local_path = unit_repo.get_local(unit_repo_path)
		else:
			unit_local_path = unit_repo.create_local(unit_repo_path)

		cmd = " ".join([
			python_bin, conf["bin_paths.matrix_join"],
			"-o '%s'" % unit_local_path,
			"-C '${filename_noext}'",
			"--skip-empty",
			" ".join(files)])

		log.debug(cmd)

		retcode = subprocess.call(args = cmd, shell = True)

		if retcode != 0:
			log.error("There was an error joining matrices:\n%s" % "\n".join(files))
			continue

		for i in xrange(len(files)):
			repos[i].close_local(files[i])

		unit_repo.put_local(unit_local_path)

		df = u["data_file"] = u.create_element()
		df["repo"] = unit_repo.name()
		df["path"] = os.path.dirname(unit_repo_path)
		df["file"] = os.path.basename(unit_repo_path)

		em.persist(u, types.MRNA_LOG2R_TUMOUR_UNIT)
		joined_log2r_tumour_unit_port.write(uid)
	
	em.close()

	data_repo.close()
	
if __name__ == "__main__":
	Task(run).start()
