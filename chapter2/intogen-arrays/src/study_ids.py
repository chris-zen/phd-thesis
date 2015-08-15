from wok.task import Task

from intogen.data.entity.server import EntityServer
from intogen.data.entity import types

def run(task):

	# Initialization

	conf = task.conf

	log = task.logger()

	task.check_out_ports(["study_ids"])

	study_ids_port = task.ports["study_ids"]

	es = EntityServer(conf["entities"])
	em = es.manager()

	# Run

	log.info("Reading studies ...")

	count = 0
	for id in em.find_ids(types.SOURCE_STUDY):
		study_ids_port.write(id)
		count += 1

	log.info("{0} studies found".format(count))

	return 0

if __name__ == "__main__":
	Task(run).start()