import os
import sys
import re
import subprocess

from intogensm.exceptions import InternalError

PROJECT_NAME = "intogen-mutations"

MUTATIONS_FLOW_NAME = "analysis"
DRIVERS_FLOW_NAME = "drivers"
COMBINATION_FLOW_NAME = "combination"
RESULTS_FLOW_NAME = "results"
QC_FLOW_NAME = "qc"
SUMMARY_FLOW_NAME = "summary"

DEFAULT_PLATFORM_NAME = "default"

def init_project_files(project, base_path=None, file_object=None, check_paths=True):
	"""
	Initializes a project definition, validates attributes and prepares storage object names.
	:param log: logger
	:param project: the project definition
	:param base_path: the path where looking for relative file references
	:param file_object: a dictionary with (variants file path) <-> (storage object name)
	:return: the project definition
	"""
	next_name_index = {}
	storage_objects = []
	project_files = project["files"]
	for i, var_file in enumerate(project_files):
		if check_paths:
			if not os.path.isabs(var_file):
				var_file = os.path.join(base_path or os.getcwd(), var_file)
			if not os.path.exists(var_file):
				raise Exception("Variants file not found for project {}: {}".format(project["id"], var_file))

			# avoid duplicated storage objects when the same file is used in several projects
			var_file = os.path.realpath(var_file)
			if file_object is not None and var_file in file_object:
				storage_objects += [file_object[var_file]]
				continue

			project_files[i] = var_file

		basename = os.path.basename(var_file)
		if basename in next_name_index:
			name, ext = split_ext(basename)
			basename = "{}-{:02}.{}".format(name, next_name_index[basename], ext)
			next_name_index[basename] += 1
		else:
			next_name_index[basename] = 2

		obj_name = "sources/{}/{}".format(project["id"], basename)
		storage_objects += [obj_name]
		if file_object is not None and check_paths:
			file_object[var_file] = obj_name

	project["storage_objects"] = storage_objects

	return project

def upload_files(log, case_name, containers, projects, streams=None):
	uploaded = set()
	log.info("[{}] Uploading variant files ...".format(case_name))
	#storages = set()
	for container in containers:
		# TODO avoid uploading to the same storage again
		#if storage.name in storages:
		#	continue
		#storages.add(storage.name)
		for project in projects:
			flen = len(project["files"])
			assert flen == len(project["storage_objects"])
			assert streams is None or len(streams) == flen
			for i, var_file, obj_name in zip(range(flen), project["files"], project["storage_objects"]):
				basename = os.path.basename(var_file)
				log.debug("[{}]   {}::{} --> {}::{} ...".format(
					case_name, project["id"], basename, container.storage.name, obj_name))

				# avoid uploading many times to the same object
				if obj_name in uploaded:
					continue
				uploaded.add(obj_name)

				if container.exists_object(obj_name):
					obj = container.get_object(obj_name)
				else:
					obj = container.create_object(obj_name)

				obj.put_data(var_file if streams is None else streams[i])

def download_files(log, case_name, containers, prefix, target_path):
	log.info("[{}] Downloading results ...".format(case_name))
	log.debug("> {}".format(target_path))

	storages = set()
	for container in containers: # FIXME what to do with multiple/repeated containers ?
		storage_name = container.storage.name
		if storage_name in storages:
			continue
		storages.add(storage_name)
		container.download(target_path, prefix=prefix,
						   start_callback=lambda name: log.debug(
							   "[{}]   {}::{} ...".format(case_name, storage_name, name)))

	log.debug("[{}] Looking for databases to decompress ...".format(case_name))

	for path, folders, files in os.walk(target_path):
		for filename in files:
			if filename == "project.db.gz":
				log.debug("[{}]   {}".format(case_name, os.path.basename(path)))
				retcode = subprocess.call(["gunzip", "-f", os.path.join(path, filename)])