from wok.task import Task

from intogen.data.entity.server import EntityServer
from intogen.repository.server import RepositoryServer
from intogen.repository import rpath
from intogen.data.entity import types

task = Task()

@task.main()
def main():

	# Initialization

	conf = task.conf

	log = task.logger()

	es = EntityServer(conf["entities"])
	em = es.manager()

	rs = RepositoryServer(conf["repositories"])
	data_repo = rs.repository("data")

	# Run

	for k, v in vars(types).items():
		if k.startswith("MRNA_"):
			log.info("Preparing '{0}' ...".format(v))
			em.ensure_collection_exists(v)
			path = rpath.absolute(v.replace(".", "/"))
			log.debug("\tData: {0}".format(path))
			data_repo.mkdir_if_not_exists(path)

	em.close()
	es.close()
	data_repo.close()
	rs.close()
	
	return 0

task.start()