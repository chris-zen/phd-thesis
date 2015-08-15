from wok.logger import get_logger

from intogensm.utils import match_id, list_projects

class ProjectsLoader(object):
	def __init__(self, paths, includes=None, excludes=None, ignore_duplicates=False):
		self.paths = paths

		self.includes = includes if includes is None or len(includes) == 0 else ["^.*$"]
		self.excludes = excludes if excludes is not None else []

		self.ignore_duplicates = ignore_duplicates

	def __format_project(self, log, project, base_path=None):
		project_id = project["id"]

		if "annotations" in project:
			annotations = project["annotations"]
			if not isinstance(annotations, dict):
				log.warn("Overriding project annotations field with an empty dictionary")
				project["annotations"] = annotations = {}
		else:
			project["annotations"] = annotations = {}

		for key in project.keys():
			if key not in ["id", "assembly", "files", "annotations", "oncodriveclust", "oncodrivefm"]:
				value = project[key]
				del project[key]
				annotations[key] = value

		if "assembly" not in project:
			project["assembly"] = "hg19"

		files = project["files"]

		# make absolute paths if necessary
		if base_path is not None:
			for i, filename in enumerate(files):
				if not os.path.isabs(filename):
					files[i] = os.path.join(base_path, filename)

		missing_files = []

		for filename in files:
			if not os.path.isfile(filename):
				missing_files += [filename]

		if len(missing_files) > 0:
			raise Exception("Project {0} references some missing files:\n{1}".format(project_id, "\n".join(missing_files)))

	def load(self):
		log = get_logger(__name__)

		log.info("Loading project data definitions ...")
		log.debug("Paths:\n{0}".format("\n  ".join(self.paths)))
		log.debug("Includes:\n{0}".format("\n  ".join(self.includes)))
		log.debug("Excludes:\n{0}".format("\n  ".join(self.excludes)))

		# compile regular expressions

		includes = [re.compile(inc) for inc in self.includes]
		excludes = [re.compile(exc) for exc in self.excludes]

		# scan paths

		project_ids = set()
		projects = []

		for scan_path in self.paths:
			for path, project in list_projects(log, scan_path):
				if "id" not in project:
					log.warn("Discarding project that doesn't have 'id': {0}".format(path))
					continue
				if "files" not in project:
					log.warn("Discarding project that doesn't have 'files': {0}".format(path))
					continue

				project_id = project["id"]

				project_name = ": " + project["name"] if "name" in project else ""

				if match_id(project_id, includes) and not match_id(project_id, excludes):
					if project_id in project_ids:
						msg = "Duplicated project id at {0}".format(path)
						if self.ignore_duplicates:
							log.warn(msg)
							continue
						else:
							raise Exception(msg)

					log.info("Included {0}{1}".format(project_id, project_name))

					self.__format_project(log, project, base_path=os.path.dirname(path))

					projects += [project]
				else:
					log.info("Excluded {0}{1}".format(project_id, project_name))

		return projects