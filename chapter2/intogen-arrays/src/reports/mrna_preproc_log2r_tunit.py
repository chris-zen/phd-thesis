import subprocess

from wok.task import Task

from intogen.data.entity import types
from intogen.repository.server import RepositoryServer
from intogen.data.entity.server import EntityServer

task = Task()

@task.main()
def main():

	# Initialization

	task.check_conf(["entities"])
	conf = task.conf

	log = task.logger()

	id_port = task.ports("mrna_normal_pool")

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])
	data_repo = rs.repository("data")

	overwrite = conf.get("overwrite", False, dtype=bool)

	results_base_path = "reports/" + types.CNV_COMBINATION.replace(".", "/")

	# Run

	for id in id_port:
		e = em.find(oid, types.MRNA_LOG2R_TUMOUR_UNIT)
		if e is None:
			log.error("{} not found: {}".format(types.MRNA_LOG2R_TUMOUR_UNIT, id))
			continue

		repo, data_path = rs.from_url(e["data_file"])
		data_local_path = repo.get_local(data_path)

		cmd = " ".join([conf["bin_paths.R"],
			"--vanilla --slave -f", script,
			"--args", results_base_path, id, data_local_path])

		log.debug(cmd)

		retcode = subprocess.call(args = cmd, shell = True)

		if retcode != 0:
			raise Exception("R script failed")

		repo.close_local(data_local_path)
		repo.close()

	em.close()
	es.close()

task.start()