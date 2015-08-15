from wok.task import Task

from intogen.data.entity import types
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

	# Run



	em.close()
	es.close()

task.start()