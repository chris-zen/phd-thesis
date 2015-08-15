from wok.task import Task

from intogen.data.entity.server import EntityServer

task = Task()

@task.main()
def main():

	# Initialization

	conf = task.conf

	etype = conf["etype"]

	log = task.logger()

	port = task.ports["id"]

	es = EntityServer(conf["entities"])
	em = es.manager()

	# Run

	log.info("Reading '{0}' ...".format(etype))

	count = 0
	for id in em.find_ids(etype):
		port.write(id)
		count += 1

	log.info("{0} entities found".format(count))

	return 0

task.start()