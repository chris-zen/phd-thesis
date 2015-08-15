import sys
import os
import json
import getpass
import signal

from argparse import ArgumentParser, RawDescriptionHelpFormatter

from datetime import datetime

from wok import logger
from wok.config.data import Data
from wok.config.builder import ConfigBuilder
from wok.engine import WokEngine

from intogensm import VERSION
from intogensm.utils import normalize_id
from intogensm.config import GlobalConfig, PathsConfig
from intogensm.analysis import (PROJECT_NAME, DEFAULT_PLATFORM_NAME,
								upload_files, download_files)

def keyboardinterrupt_handler(*args):
	raise KeyboardInterrupt

class Command(object):
	def __init__(self, args_usage="", epilog="", logger_name=None):

		self.args_usage = args_usage
		self.epilog = epilog

		if logger_name is None:
			if hasattr(self, "cmd_name"):
				logger_name = self.cmd_name
			else:
				logger_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]

		# Determine binary path

		script_path = os.path.dirname(sys.argv[0])
		if script_path:
			self.launchers_path = os.path.abspath(script_path)
		else:
			self.launchers_path = os.getcwd()

		# Determine default paths

		self.root_path = os.path.normpath(os.path.join(self.launchers_path, ".."))
		self.conf_path = os.path.join(self.root_path, "conf")
		self.runtime_path = os.path.join(self.root_path, "runtime")

		# Parse arguments

		parser = ArgumentParser(
			prog = "run " + self.cmd_name,
			epilog = self.epilog,
			formatter_class=RawDescriptionHelpFormatter)

		parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

		self.add_arguments(parser)

		parser.add_argument("-L", "--log-level", dest="log_level",
						  default=None, choices=["debug", "info", "warn", "error", "critical", "notset"],
						  help="Define the logging level")

		self.args = parser.parse_args()

		# Create preliminary logger

		level = self.args.log_level or "info"
		logger.initialize(level=level)


		self.log = logger.get_logger(logger_name, level=level)

	def add_arguments(self, parser):
		"Called from __init__() to let the command to add more options to the OptionsParser"
		pass

	def execute(self):
		"Called from run() when the configuration is ready"
		raise NotImplementedError()

	def run(self):
		"Main entry point"

		self.execute()

class ConfArgs(object):
	def __init__(self, logger, path, args_files, args_data, req_files=[], req_keys=[]):
		self.log = logger
		self.conf_path = path

		self.conf_keys = req_keys

		self.required_conf_files = [os.path.join(self.conf_path, cf) for cf in req_files]

		self.conf_files = []
		if args_files is not None:
			for cf in args_files:
				if not os.path.isabs(cf):
					cf = os.path.join(os.getcwd(), cf)
				self.conf_files += [cf]

		self.conf_data = args_data or []

		self.conf_builder = ConfigBuilder()

	def load_files(self):
		"Called from run() to prepare configuration before expansion of values"

		conf_files = self.required_conf_files

		user_conf_file = os.path.join(self.conf_path, "user.conf")
		if os.path.exists(user_conf_file):
			conf_files += [user_conf_file]

		conf_files += self.conf_files

		# Check that configuration files exist

		missing_conf_files = [cf for cf in conf_files if not os.path.exists(cf)]
		if len(missing_conf_files) > 0:
			self.log.error("Configuration files not found:\n{}".format(
							"\n".join("  {}".format(cf) for cf in missing_conf_files)))
			exit(-1)

		for cf in conf_files:
			self.conf_builder.add_file(cf)

		return self.conf_builder

	def parse_data(self):
		for data in self.conf_data:
			try:
				pos = data.index("=")
				key = data[0:pos]
				value = data[pos+1:]
				try:
					v = json.loads(value)
				except:
					v = value
				self.conf_builder.add_value(key, v)
			except:
				raise Exception("Wrong configuration data: KEY=VALUE expected but found '{}'".format(data))

		return self.conf_builder

	def validated_conf(self, expand_vars=True):
		self.conf = self.conf_builder.get_conf()
		if expand_vars:
			self.conf.expand_vars()

		#self.log.debug(repr(self.conf))

		# Validate that required keys exist

		mk = self.conf.missing_keys(self.conf_keys)
		if len(mk) > 0:
			sb = ["The following configuration parameters were not found:\n",
					"\n".join("* " + k for k in mk),
					"\nin any of the following configuration files:\n",
					"\n".join("* " + k for k in conf_files)]
			self.log.error("".join(sb))
			exit(-1)

		return self.conf

	def log_debug(self):
		if len(self.conf_files) > 0:
			self.log.debug("User defined configuration files:\n{}".format(
							"\n".join("  {}".format(cf) for cf in self.conf_files)))

		self.log.debug("Effective configuration: " + str(self.conf))

class RunCommand(Command):

	DEFAULT_CONF_FILES = [
		"system.conf", "run.conf"
	]

	DEFAULT_REQUIRED_CONF = [
#		"work_path", "temp_path"]
	]

	def __init__(self, args_usage="", epilog="", logger_name=None):

		Command.__init__(self, args_usage, epilog, logger_name)

		signal.signal(signal.SIGINT, keyboardinterrupt_handler)
		signal.signal(signal.SIGTERM, keyboardinterrupt_handler)

		'''
		# Override configuration path if required

		if self.args.conf_path is not None:
			self.conf_path = os.path.abspath(self.args.conf_path)
		'''

		# Determine required and user configuration files and data

		self.engine_conf_args = ConfArgs(self.log, self.conf_path,
										 self.args.engine_conf_files, self.args.engine_conf_data,
										 self.DEFAULT_CONF_FILES, self.DEFAULT_REQUIRED_CONF)

		self.engine_conf_builder = self.engine_conf_args.conf_builder

		self.case_conf_args = ConfArgs(self.log, self.conf_path, self.args.case_conf_files, self.args.case_conf_data)

		self.case_conf_builder = self.case_conf_args.conf_builder

		# Workspace

		self.workspace = self.args.workspace

		# Case name

		self.case_name = self.args.case_name

		if self.case_name is not None:
			self.case_name = normalize_id(self.case_name)

		# max cores

		if self.args.max_cores is None:
			self.max_cores = 0
		else:
			self.max_cores = self.args.max_cores

	def add_arguments(self, parser):
		"Called from __init__() to let the command to add more options to the OptionsParser"

		parser.add_argument("-w", "--workspace", dest = "workspace", metavar = "NAME", default="default",
						  help = "Define the workspace name.")

		parser.add_argument("-u", "--user", dest="user", metavar="NAME",
						  help="Define the user name.")

		parser.add_argument("-s", "--storage", dest="storage", metavar="NAME",
						  help="Define the storage name.")

		g = parser.add_argument_group("Wok Options")

		g.add_argument("-n", "--case", dest = "case_name", metavar = "NAME",
						  help = "Define the case name")

		g.add_argument("-c", "--engine-conf", action="append", dest="engine_conf_files", metavar="FILE",
					 help="Load engine configuration from a file. Multiple files can be specified")

		g.add_argument("-d", action="append", dest="engine_conf_data", metavar="PARAM=VALUE",
					 help="Define engine configuration parameter. Multiple definitions can be specified. Example: -d option1=value")

		g.add_argument("-C", "--conf", action="append", dest="case_conf_files", metavar="FILE",
					 help="Load case configuration from a file. Multiple files can be specified")

		g.add_argument("-D", action="append", dest="case_conf_data", metavar="PARAM=VALUE",
					 help="Define case configuration parameter. Multiple definitions can be specified. Example: -D option1=value")

		g.add_argument("-j", dest="max_cores", metavar="NUM", type=int,
					 help="Define the maximum number of cores to use. Default all the cores available.")

	def build_conf(self):
		"Called from run() to prepare configuration before expansion of values"

		# Build the configuration
			
		self.engine_conf_args.load_files()
		self.case_conf_args.load_files()

		# General conf

		if self.case_name is None:
			if self.workspace is not None:
				self.case_name = self.workspace
			else:
				self.case_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")

		if self.max_cores > 0:
			self.engine_conf_builder.add_value("wok.platforms[0].jobs.max_cores", self.max_cores)

		if self.args.log_level is not None:
			self.case_conf_builder.add_value("logging", self.args.log_level)

		# Set user and workspace

		self.user_id = self.args.user or getpass.getuser()
		self.container = self.args.storage
		self.case_conf_builder.add_value("user_id", self.user_id)
		self.case_conf_builder.add_value("workspace", self.workspace)

		# Parse conf data

		self.engine_conf_args.parse_data()
		self.case_conf_args.parse_data()

	def process_conf(self):
		"Called from run() to process the configuration after expansion of values"

		# Configure wok work path

		if "wok.work_path" not in self.engine_conf:
			self.engine_conf_builder.add_value("wok.work_path",
											   os.path.join(self.engine_conf.get("runtime_path", os.getcwd()), "wok"))

	def run(self):
		"Run the command and execute the command"

		self.build_conf()

		# Expand configuration variables

		self.engine_conf = self.engine_conf_args.validated_conf()
		self.case_conf = self.case_conf_args.validated_conf(expand_vars=False)

		# Validate and process configuration

		self.process_conf()
		
		# Regenerate configuration

		self.engine_conf = self.engine_conf_builder.get_conf()
		self.case_conf = self.case_conf_builder.get_conf()

		# Final logging configuration

		log = logger.get_logger("")
		log.removeHandler(log.handlers[0])
		logging_conf = self.engine_conf.get("wok.logging")
		logger.initialize(logging_conf)

		# Show some debugging information

		self.log.debug("Root path = {}".format(self.root_path))
		self.log.debug("Conf path = {}".format(self.conf_path))
		#self.log.debug("Runtime path = {}".format(self.runtime_path))
		#self.log.debug("Results path = {}".format(self.results_path))
		#self.log.debug("Temp path = {}".format(self.temp_path))

		self.engine_conf_args.log_debug()
		self.case_conf_args.log_debug()

		# Execute

		try:
			self.execute()
		except BaseException as ex:
			self.log.error(str(ex))
			from traceback import format_exc
			self.log.debug(format_exc())
			return -1

		return 0

	def _case_created(self, case, **kwargs):
		if hasattr(self, "projects") and self.projects is not None:
			upload_files(self.log, case.name, case.storages, self.projects)

			config = GlobalConfig(
				case.project.get_conf(platform_name=DEFAULT_PLATFORM_NAME),
				dict(user_id=self.user_id, workspace=self.workspace))

			self.results_path = PathsConfig(config).results_path()

	def _case_finished(self, case, **kwargs):
		if hasattr(self, "results_path") and self.results_path is not None:
			download_files(self.log, case.name, case.storages, "results/", self.results_path)

	def _wok_run(self, flow, case_name=None, project=None, container=None):

		# Create and start the Wok engine

		self.wok = WokEngine(self.engine_conf, self.conf_path)

		self.wok.case_created.connect(self._case_created)
		self.wok.case_finished.connect(self._case_finished)

		self.wok.start(wait=False, single_run=True)

		# Create and start the case

		try:
			case_name = case_name or self.case_name

			case = self.wok.create_case(
				case_name,
				self.case_conf_builder,
				project or PROJECT_NAME,
				flow,
				container or self.container or case_name)

			case.start()

			self.wok.wait()
		except KeyboardInterrupt:
			pass
		finally:
			try:
				self.wok.stop()
			except KeyboardInterrupt:
				self.log.warn("Ctrl-C pressed while stopping Wok engine.")