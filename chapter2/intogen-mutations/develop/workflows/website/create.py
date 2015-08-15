import os
import shutil

from string import Template

from wok.task import task

from intogensm.config import GlobalConfig, PathsConfig

@task.foreach()
def create(project):
	log = task.logger

	config = GlobalConfig(task.conf)
	paths = PathsConfig(config)

	project_id = project["id"]

	log.info("--- [{0}] --------------------------------------------".format(project_id))

	project_path = project["path"]
	temp_path = project["temp_path"]

	templates_path = config.website.templates_path
	if templates_path is None:
		log.warn("No website templates have been defined in the configuration. Skipping website creation.")
		return

	log.info("Creating website ...")

	website_path = paths.project_website_path(project_path)
	if os.path.exists(website_path):
		shutil.rmtree(website_path)

	log.info("Copying templates ...")

	shutil.copytree(templates_path, website_path)

	gitignore_path = os.path.join(website_path, ".gitignore")
	try:
		os.remove(gitignore_path)
	except:
		pass

	log.info("Expanding templates ...")

	vars = dict(
		PROJECT_NAME=project_id,
		SHOW_ALL_TABS=not config.variants_only)

	tmpl_paths = [
		os.path.join(website_path, "css", "header.html"),
		os.path.join(website_path, "onexus-project.onx")
	]

	for path in tmpl_paths:
		with open(path, "r") as f:
			t = Template(f.read())
		with open(path, "w") as f:
			f.write(t.safe_substitute(vars))

	# Creating a soft link to the results folder
	project_results_path = paths.project_results_path(project_path)
	os.symlink(project_results_path, os.path.join(website_path, "results"))

	# Send project to the next modules

	projects_port = task.ports("projects_out")
	project["website"] = website_path
	projects_port.send(project)

task.run()