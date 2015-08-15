import os
import re

from intogensm.command import RunCommand
from intogensm.command.analysis import PROJECT_EPILOG
from intogensm.analysis import MUTATIONS_FLOW_NAME, init_project_files
from intogensm.utils import match_id, list_projects, normalize_id


class BatchAnalysisCommand(RunCommand):

	cmd_name = "batch-analysis"

	def __init__(self):
		RunCommand.__init__(self,
			args_usage="<projects-path> [<projects-path> ...]",
			epilog=PROJECT_EPILOG)

	def add_arguments(self, parser):
		RunCommand.add_arguments(self, parser)

		parser.add_argument("paths", nargs="+",
							help="Projects paths")

		parser.add_argument("-i", "--include", dest = "include", metavar = "ID", action="append",
			help = "Include project which id=ID")

		parser.add_argument("-I", "--include-regex", dest = "include_regex", metavar = "REGEX", action="append",
			help = "Include project which id matches REGEX")

		parser.add_argument("--include-from", dest = "include_from", metavar = "FILE", action="append",
			help = "Include project which id found in file FILE")

		parser.add_argument("-e", "--exclude", dest = "exclude", metavar = "ID", action="append",
			help = "Exclude project which id=ID")

		parser.add_argument("-E", "--exclude-regex", dest = "exclude_regex", metavar = "REGEX", action="append",
			help = "Exclude project which id matches REGEX")

		parser.add_argument("--exclude-from", dest = "exclude_from", metavar = "FILE", action="append",
			help = "Exclude project which id found in file FILE")
		
	def build_conf(self):
		super(BatchAnalysisCommand, self).build_conf()

	def execute(self):

		# Gather scan paths from arguments

		scan_paths = []

		for scan_path in self.args.paths:
			if not os.path.isabs(scan_path):
				scan_path = os.path.join(os.getcwd(), scan_path)

			if not os.path.exists(scan_path):
				self.log.error("Path not found: {}".format(scan_path))
				exit(-1)

			scan_paths += [scan_path]

		# Gather includes and excludes from options

		includes = []

		if self.args.include is not None:
			for inc in self.args.include:
				includes += ["^{0}$".format(re.escape(inc))]
		if self.args.include_regex is not None:
			for inc_regex in self.args.include_regex:
				includes += [inc_regex]
		if self.args.include_from is not None:
			for file in self.args.include_from:
				with open(file, "r") as f:
					for line in f:
						line = line.strip()
						if line.startswith("#") or len(line) == 0:
							continue
						includes += ["^{0}$".format(re.escape(line))]

		if len(includes) == 0:
			includes = ["^.*$"]

		excludes = []

		if self.args.exclude is not None:
			for exc in self.args.exclude:
				excludes += ["^{0}$".format(re.escape(exc))]
		if self.args.exclude_regex is not None:
			for exc_regex in self.args.exclude_regex:
				excludes += [exc_regex]
		if self.args.exclude_from is not None:
			for file in self.args.exclude_from:
				with open(file, "r") as f:
					for line in f:
						line = line.strip()
						if line.startswith("#") or len(line) == 0:
							continue
						excludes += ["^{0}$".format(re.escape(line))]

		# compile regular expressions

		includes = [re.compile(inc) for inc in includes]
		excludes = [re.compile(exc) for exc in excludes]

		# scan paths

		self.projects = []
		project_ids = set()
		file_object = {}

		self.log.info("Looking for data projects ...")

		for scan_path in scan_paths:
			for path, project in list_projects(self.log, scan_path):
				if "id" not in project:
					self.log.warn("Discarding project missing 'id': {0}".format(path))
					continue
				if "files" not in project:
					self.log.warn("Discarding project missing 'files': {0}".format(path))
					continue

				project["id"] = normalize_id(project["id"])
				project_id = project["id"]
				if "name" in project:
					project_name = ": " + project["name"]
				else:
					project_name = ""

				if match_id(project_id, includes) and not match_id(project_id, excludes):
					if project_id in project_ids:
						self.log.error("Duplicated project id at {0}".format(path))
						exit(-1)

					self.log.info("  {0}{1} (included)".format(project_id, project_name))

					project = init_project_files(project, os.path.dirname(path), file_object)
					self.projects += [project]
				else:
					self.log.info("  {0}{1} (excluded)".format(project_id, project_name))

		# Create the wok engine and the workflow instance
		
		self.case_conf_builder.add_value("projects", self.projects)

		self._wok_run(MUTATIONS_FLOW_NAME, container="{}-{}".format(self.user_id, self.workspace))
