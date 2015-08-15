import re
from wok.task import Task

from intogen.data.entity import types
from intogen.data.entity.server import EntityServer

task = Task()

def extract(log, em, etype, *info_sets, **kargs):

	log.info("Reading '{}' ...".format(etype))

	if "excludes" in kargs:
		excludes = kargs["excludes"]
		if excludes is not None:
			for exclude in excludes:
				if isinstance(exclude[1], basestring):
					log.debug("exclude {} like {}".format(exclude[0], exclude[1]))
					exclude[1] = re.compile(exclude[1])
	else:
		excludes = None

	count = 0
	for id in em.find_ids(etype):
		e = em.find(id, etype)
		if e is None:
			log.error("{} not found: {}".format(etype, id))
			continue

		if excludes is not None:
			excluded = False
			for exclude in excludes:
				if exclude[0] in e:
					if exclude[1].match(e[exclude[0]]) is not None:
						excluded = True
						break
			if excluded:
				continue

		log.debug("{} [{}]".format(etype, id))
		
		for iset in info_sets:
			bag = iset[0]
			keys = iset[1]
			if not isinstance(keys, tuple):
				keys = tuple([keys])
			values = [e[k] for k in keys]
			bag.add(tuple(values))

		count += 1

	log.info("{} entities found".format(count))

@task.main()
def main():

	# Initialization

	task.check_conf(["entities"])
	conf = task.conf

	log = task.logger()

	icdo_port, exp_port = task.ports(["icdo", "experiment"])

	mrna_oncodrive_gene_port, mrna_enrichment_port, mrna_combination_port = \
		task.ports(["mrna_oncodrive_gene", "mrna_enrichment", "mrna_combination"])

	cnv_oncodrive_gene_port, cnv_enrichment_port, cnv_combination_port = \
		task.ports(["cnv_oncodrive_gene", "cnv_enrichment", "cnv_combination"])

	es = EntityServer(conf["entities"])
	em = es.manager()

	# Run

	exp = set()
	icdo = set()

	excludes = None
	if "biomart.excludes" in conf:
		excludes = conf["biomart.excludes"]

	# mrna oncodrive genes
	results = set()
	extract(log, em, types.MRNA_ONCODRIVE_GENES,
		(results, ("id")),
		(exp, ("study_id", "platform_id")),
		(icdo, ("icdo_topography", "icdo_morphology")),
		excludes = excludes)

	log.info("Sending {} ids ...".format(types.MRNA_ONCODRIVE_GENES))
	for rid, in results:
		mrna_oncodrive_gene_port.write(rid)

	# mrna enrichment
	results = set()
	extract(log, em, types.MRNA_ENRICHMENT,
		(results, ("id_type", "id")),
		(icdo, ("icdo_topography", "icdo_morphology")),
		excludes = excludes)

	log.info("Sending {} ids ...".format(types.MRNA_ENRICHMENT))
	for r in sorted(results):
		mrna_enrichment_port.write(r)

	# mrna combination
	results = set()
	extract(log, em, types.MRNA_COMBINATION,
		(results, ("id_type", "id")),
		(icdo, ("icdo_topography", "icdo_morphology")),
		excludes = excludes)

	log.info("Sending {} ids ...".format(types.MRNA_COMBINATION))
	for r in sorted(results):
		mrna_combination_port.write(r)

	# cnv oncodrive genes
	results = set()
	extract(log, em, types.CNV_ONCODRIVE_GENES,
		(results, ("id")),
		(exp, ("study_id", "platform_id")),
		(icdo, ("icdo_topography", "icdo_morphology")),
		excludes = excludes)

	log.info("Sending {} ids ...".format(types.CNV_ONCODRIVE_GENES))
	for rid, in results:
		cnv_oncodrive_gene_port.write(rid)

	# cnv enrichment
	results = set()
	extract(log, em, types.CNV_ENRICHMENT,
		(results, ("id_type", "id")),
		(icdo, ("icdo_topography", "icdo_morphology")),
		excludes = excludes)

	log.info("Sending {} ids ...".format(types.CNV_ENRICHMENT))
	for r in sorted(results):
		cnv_enrichment_port.write(r)

	# cnv combination
	results = set()
	extract(log, em, types.CNV_COMBINATION,
		(results, ("id_type", "id")),
		(icdo, ("icdo_topography", "icdo_morphology")),
		excludes = excludes)

	log.info("Sending {} ids ...".format(types.CNV_COMBINATION))
	for r in sorted(results):
		cnv_combination_port.write(r)

	# icdo

	log.info("Sending icdo's ...")
	for tm in icdo:
		icdo_port.write(tm)

	# exp

	log.info("Sending experiments ...")
	for e in exp:
		exp_port.write(e)

	em.close()
	es.close()

task.start()