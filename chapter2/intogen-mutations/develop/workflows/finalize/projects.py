import os
import shutil
import tempfile
import subprocess

from wok.task import task

from intogensm.config import GlobalConfig, PathsConfig
from intogensm.projects.results import ProjectResults

@task.foreach()
def finalize_project(project):
	log = task.logger

	config = GlobalConfig(task.conf)
	paths = PathsConfig(config)

	project_id = project["id"]

	log.info("--- [{0}] --------------------------------------------".format(project_id))

	log.info("Cleaning project ...")

	projres = ProjectResults(project)

	projres.clean(config)

	log.info("Saving project configuration ...")

	projres.save_def()

	if config.results.use_storage:
		log.info("Compressing the database ...")

		db_path = os.path.join(projres.path, "project.db")
		temp_path = tempfile.mkdtemp(prefix="intogen-mutations-{}-".format(project_id))
		compressed_db_path = os.path.join(temp_path, "project.db.gz")

		try:
			cmd = "gzip -c {} >{}".format(db_path, compressed_db_path)

			log.debug("> {}".format(cmd))

			retcode = subprocess.call(cmd, shell=True)
			if retcode == 1:
				raise Exception("Error compressing the project database")

			log.info("Uploading project files ...")

			exclude = ["sources/*", "project.db", "project.db.gz"]
			if not config.results.create_zip:
				exclude += ["results.zip"]

			object_prefix = "results/projects/{}".format(project_id)
			start_callback = lambda path: log.info("  {}".format(path))

			if os.path.exists(compressed_db_path):
				task.storage.upload(compressed_db_path, object_prefix=object_prefix, overwrite=True,
									start_callback=start_callback)

			task.storage.upload(projres.path, object_prefix=object_prefix, exclude=exclude, overwrite=True,
								start_callback=start_callback)

			if config.results.purge_after_upload:
				log.info("Purging project files ...")
				shutil.rmtree(projres.path)

		finally:
			if os.path.exists(temp_path):
				shutil.rmtree(temp_path)

task.run()