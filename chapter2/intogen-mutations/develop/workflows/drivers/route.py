import os

from wok.task import task

from intogensm.config import GlobalConfig, PathsConfig

@task.begin()
def begin():
	log = task.logger

	config = GlobalConfig(task.conf)

	log.info("Routing projects into analysis ...")
	log.info("  skip_recurrences = {0}".format(config.skip_recurrences))
	log.info("  skip_oncodrivefm = {0}".format(config.skip_oncodrivefm))
	log.info("  skip_oncodriveclust = {0}".format(config.skip_oncodriveclust))
	log.info("")

@task.foreach()
def route(project):
	log = task.logger

	config = GlobalConfig(task.conf)

	projects_port = task.ports("projects_out")
	recurrences_projects_port = task.ports("recurrences_projects")
	oncodrivefm_projects_port = task.ports("oncodrivefm_projects")
	oncodriveclust_projects_port = task.ports("oncodriveclust_projects")

	log.info("  {0}".format(project["id"]))

	projects_port.send(project)

	if not config.skip_recurrences:
		recurrences_projects_port.send(project)

	if not config.skip_oncodrivefm:
		oncodrivefm_projects_port.send(project)

	if not config.skip_oncodriveclust:
		oncodriveclust_projects_port.send(project)

task.run()