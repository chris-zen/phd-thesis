from wok.task import task

from intogensm.projects.db import ProjectDb
from intogensm.projects.results import ProjectResults

@task.foreach()
def variants(project):
	log = task.logger

	log.info("--- [{0}] --------------------------------------------".format(project["id"]))

	log.info("Calculating number of variants processed in each step ...")

	proj_res = ProjectResults(project)

	projdb = ProjectDb(project["db"])

	counts = projdb.count_variants()

	proj_res.save_quality_control("variants", counts)

	projdb.close()

task.run()