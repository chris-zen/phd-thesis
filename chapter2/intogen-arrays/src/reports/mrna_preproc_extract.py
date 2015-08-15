from wok.task import Task

from intogen.utils import extract_from_entities
from intogen.data.entity import types
from intogen.data.entity.server import EntityServer

task = Task()

def extract_and_send(log, em, etype, port):
	results = set()
	extract_from_entities(log, em, etype,
		(results, ("id")))

	log.info("Sending {} {} ids ...".format(len(results), etype))
	for rid, in results:
		port.write(rid)

@task.main()
def main():

	# Initialization

	task.check_conf(["entities"])
	conf = task.conf

	log = task.logger()

	mrna_log2r_tunit_port, mrna_normal_pool_port = \
		task.ports(["mrna_log2r_tunit", "mrna_normal_pool"])

	es = EntityServer(conf["entities"])
	em = es.manager()

	# Run

	# mrna preprocessing

	extract_and_send(log, em, types.MRNA_NORMAL_POOL, mrna_normal_pool_port)

	extract_and_send(log, em, types.MRNA_LOG2R_TUMOUR_UNIT, mrna_log2r_tunit_port)

	em.close()
	es.close()

task.start()