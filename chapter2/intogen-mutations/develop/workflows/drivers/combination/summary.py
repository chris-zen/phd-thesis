import os

from wok.task import task

from bgcore import tsv

from intogensm.utils import normalize_id
from intogensm.config import GlobalConfig, PathsConfig
from intogensm.projects.db import ProjectDb

@task.foreach()
def datasets(projects_set):
	log = task.logger

	config = GlobalConfig(task.conf)
	paths = PathsConfig(config)

	classifier, projects = projects_set

	classifier_id = classifier["id"]

	group_values = classifier["group_values"]
	short_values = classifier["group_short_values"]
	long_values = classifier["group_long_values"]

	group_name = classifier["group_name"]
	group_short_name = classifier["group_short_name"]
	group_long_name = classifier["group_long_name"]

	group_file_prefix = normalize_id(classifier_id)

	log.info("--- [{0} ({1}) ({2}) ({3})] {4}".format(
		classifier["name"], group_long_name, group_short_name, group_name, "-" * 30))

	log.info("Reading number of samples per project ...")

	project_ids = []
	total_samples = 0
	for project in projects:
		project_id = project["id"]
		project_ids += [project_id]

		log.info("  Project {0}".format(project["id"]))

		projdb = ProjectDb(project["db"])

		num_samples = projdb.get_total_affected_samples()
		total_samples += num_samples

		log.debug("    {0} samples".format(num_samples))

		projdb.close()

	log.debug("  {0} samples in total".format(total_samples))

	log.info("Updating ...")

	combination_path = paths.combination_path()

	path = os.path.join(combination_path, "{0}.tsv".format(group_file_prefix))

	if not os.path.exists(path):
		with open(path, "w") as f:
			tsv.write_line(f, "NAME", "SHORT_NAME", "LONG_NAME", "SAMPLES_TOTAL", "PROJECT_IDS")

	with open(path, "a") as f:
		tsv.write_line(f, group_name, group_short_name, group_long_name, total_samples, ",".join(project_ids))

task.run()