import os
import shutil

from wok.task import task
from wok.config.data import Data

from intogensm.config import GlobalConfig, PathsConfig
from intogensm.config import PathsConfig, create_combination_folders
from intogensm.exceptions import InternalError
from intogensm.projects.results import ProjectResults
from intogensm.projects.defaults import DEFAULT_ASSEMBLY
from intogensm.pathutils import ensure_path_exists

def validate_project(log, project):
	#TODO check missing fields: id, assembly, files, ...
	return project

def init_project(logger, config, paths, storage, project):
	project_id = project["id"]

	results_path = paths.results_path()
	project_path = paths.project_path(project_id)
	project_temp_path = paths.project_temp_path(project_path)

	if config.results.purge_on_start:
		logger.info("  Purging previous results ...")
		if os.path.isdir(project_path):
			logger.info("    {} ...".format(os.path.relpath(project_path, results_path)))
			shutil.rmtree(project_path)
		#if os.path.isdir(project_temp_path):
		#	logger.info("    {} ...".format(os.path.relpath(project_temp_path, results_path)))
		#	shutil.rmtree(project_temp_path)

		for obj_name in storage.list_objects(prefix="results/"):
			logger.info("    {} ...".format(obj_name))
			storage.delete_object("results/{}".format(obj_name))

	ensure_path_exists(project_path)
	ensure_path_exists(project_temp_path)

	projdb_path = os.path.join(project_path, "project.db")

	if "annotations" in project:
		annotations = project["annotations"]
		if not Data.is_element(annotations):
			logger.warn("Overriding project annotations field with an empty dictionary")
			project["annotations"] = annotations = Data.element()
	else:
		project["annotations"] = annotations = Data.element()

	# for backward compatibility
	for key in project.keys():
		if key not in ["id", "assembly", "files", "storage_objects", "annotations", "conf", "oncodriveclust", "oncodrivefm"]:
			value = project[key]
			del project[key]
			annotations[key] = value

	project["conf"] = pconf = project.get("conf") or Data.element()
	if not Data.is_element(pconf):
		logger.warn("Overriding project conf field with an empty dictionary")
		project["conf"] = pconf = Data.element()

	# for backward compatibility
	for key in project.keys():
		if key in ["oncodriveclust", "oncodrivefm"]:
			value = project[key]
			del project[key]
			pconf[key] = value

	project["path"] = project_path
	project["temp_path"] = project_temp_path
	project["db"] = projdb_path

	if "assembly" not in project:
		project["assembly"] = DEFAULT_ASSEMBLY

	missing_objects = []

	for obj_name in project["storage_objects"]:
		if not storage.exists_object(obj_name):
			missing_objects += [obj_name]

	if len(missing_objects) > 0:
		raise InternalError("Project {0} references some missing objects:\n{1}".format(project_id, "\n".join(missing_objects)))

	project["files"] = [str(f) for f in project["files"]] #unicode is not json serializable
	project["storage_objects"] = [str(f) for f in project["storage_objects"]] #unicode is not json serializable

	project = project.to_native()

	# save project.conf
	projres = ProjectResults(project)
	projres.save_def()

	return project

@task.source()
def scan_projects(projects_port):
	log = task.logger
	conf = task.conf

	config = GlobalConfig(conf)

	log.debug("Configuration:")
	log.debug(config)

	log.info("Creating combination folders ...")

	paths = PathsConfig(config)

	create_combination_folders(conf)

	if "projects" not in conf or not Data.is_list(conf["projects"]):
		raise InternalError("Required 'projects' configuration parameter has not been found or it is not well defined")

	log.info("Initializing projects ...")
	for project in conf["projects"]:
		if project is None:
			continue

		project = validate_project(log, project)
		project.expand_vars(conf)

		log.info("--- [{}] ---------------------------------------------------".format(project["id"]))
		project = init_project(log, config, paths, task.storage, project)
		log.info("  assembly: {}, variant_files: {}".format(project["assembly"], len(project["files"])))

		projects_port.send(project)

task.run()