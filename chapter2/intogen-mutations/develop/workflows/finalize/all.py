import shutil

from wok.task import task

from intogensm.config import GlobalConfig, PathsConfig

@task.begin()
def finalize_all():
	log = task.logger

	config = GlobalConfig(task.conf)
	paths = PathsConfig(config)

	if config.results.use_storage:
		log.info("Uploading combination files ...")

		combination_path = paths.combination_path()

		exclude = ["sources/*", "project.db", "project.db.gz"]

		object_prefix = "results/combination"
		start_callback = lambda path: log.info("  {}".format(path))

		task.storage.upload(combination_path, object_prefix=object_prefix, exclude=exclude, overwrite=True,
							start_callback=start_callback)

		if config.results.purge_after_upload:
			log.info("Purging combination files ...")
			shutil.rmtree(combination_path)

task.run()