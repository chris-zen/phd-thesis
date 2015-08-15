import os

from wok.config.data import Data

from intogensm.projects.defaults import DEFAULT_ASSEMBLY
from intogensm.command import RunCommand
from intogensm.utils import normalize_id
from intogensm.analysis import MUTATIONS_FLOW_NAME, init_project_files

PROJECT_EPILOG="""
Configurable parameters:

  You will find all the available configuration parameters from

  http://www.intogen.org/analysis/mutations/help/configuration.html
"""

class AnalysisCommand(RunCommand):

	cmd_name = "analysis"

	def __init__(self):
		RunCommand.__init__(self,
			args_usage="<variants-file> [<variants-file> ...]",
			epilog=PROJECT_EPILOG)
		
		self.variants_files = []
		
		# Gather variants files from arguments

		for var_file in self.args.files:
			if not os.path.isabs(var_file):
				var_file = os.path.join(os.getcwd(), var_file)

			if not os.path.exists(var_file):
				self.log.error("Variants file not found: {}".format(var_file))
				exit(-1)

			if not os.path.isfile(var_file):
				self.log.error("A file is expected: {}".format(var_file))
				exit(-1)

			self.variants_files += [var_file]

		# Get project id

		if self.args.project_id is None:
			self.log.error("Project identifier not specified.")
			exit(-1)

		self.project_id = normalize_id(self.args.project_id)
		
	def add_arguments(self, parser):
		RunCommand.add_arguments(self, parser)

		parser.add_argument("files", nargs="+",
			help="Variants files")

		parser.add_argument("-p", "--id", dest="project_id", metavar="NAME",
			help="Define the project identifier. Required.")
		
		parser.add_argument("-a", "--assembly", dest="assembly", metavar="ASSEMBLY",
			choices=["hg18", "hg19"], default="hg19",
			help="Define the assembly [hg18, hg19]. Default is hg19.")

		parser.add_argument("--single-tumor", dest="single_tumor", action="store_true", default=False,
			help="Run a single tumor analysis instead of the regular cohort analysis.")

	def build_conf(self):
		if self.case_name is None:
			self.case_name = self.project_id

		RunCommand.build_conf(self)
		
		self.case_conf_builder.add_value("project.id", self.project_id)

		if self.args.single_tumor:
			self.case_conf_builder.add_value("variants_only", True)
			self.case_conf_builder.add_value("skip_oncodrivefm", True)
			self.case_conf_builder.add_value("skip_oncodriveclust", True)

	def execute(self):

		project = dict(
			id=self.project_id,
			assembly=self.args.assembly or DEFAULT_ASSEMBLY,
			files=self.variants_files)

		self.projects = [init_project_files(project)]

		self.case_conf_builder.add_value("projects", self.projects)

		self._wok_run(MUTATIONS_FLOW_NAME)