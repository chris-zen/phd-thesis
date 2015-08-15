import os
import shutil
import tempfile

from intogensm.config import GlobalConfig, PathsConfig

def make_temp_file(task, suffix=""):
	config = GlobalConfig(task.conf)
	return tempfile.mkstemp(
		prefix=task.id + ".",
		suffix=suffix,
		dir=config.local_temp_path)[1]

def make_temp_dir(task, suffix=""):
	config = GlobalConfig(task.conf)
	return tempfile.mkdtemp(
		prefix=task.id + ".",
		suffix=suffix,
		dir=config.local_temp_path)

def remove_temp(task, *files):
	config = GlobalConfig(task.conf)
	if config.local_temp_remove:
		if isinstance(files, basestring):
			files = [files]

		for file in files:
			if os.path.isdir(file):
				task.logger.debug("Removing temporary folder {0} ...".format(file))
				shutil.rmtree(file)
			else:
				task.logger.debug("Removing temporary file {0} ...".format(file))
				os.remove(file)