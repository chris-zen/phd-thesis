import os

import logging
from logging import Formatter
from logging.handlers import TimedRotatingFileHandler

from wok import logger
from wok.config import ConfigBuilder
from wok.config.data import Data

from intogensm.command import RunCommand

# deprecated
class WebCommand(RunCommand):

	cmd_name = "web"

	"""
	def process_conf(self):
		super(WebCommand, self).process_conf()
		
		if "workflows_path" not in self.case_conf:
			self.case_conf_builder.add_value("workflows_path", self.workflows_path)
		
		if "results_path" not in self.case_conf:
			self.case_conf_builder.add_value("results_path", self.results_path)
		
		if "temp_path" not in self.case_conf:
			self.case_conf_builder.add_value("temp_path", self.temp_path)
	"""

	def execute(self):
		# Change cwd to root path
		os.chdir(self.root_path)
		
		# Web interface
		
		wok_conf = self.engine_conf["wok"]
		server_mode = wok_conf.get("server.enabled", False, dtype=bool)
		server_host = wok_conf.get("server.host", "0.0.0.0", dtype=str)
		server_port = wok_conf.get("server.port", 5000, dtype=int)
		server_debug = wok_conf.get("server.debug", False, dtype=bool)
		server_domain = wok_conf.get("server.domain", dtype=str)
		
		#self.log.info("Running server at http://{0}:{1}".format(server_host, server_port))
		
		logs_path = os.path.join(self.runtime_path, "logs")
		if not os.path.exists(logs_path):
			os.makedirs(logs_path)
		logs_path = os.path.join(logs_path, "server.log")
		
		rotating_handler = TimedRotatingFileHandler(logs_path, when="midnight", interval=1)
		rotating_handler.setLevel(logging.INFO)
		rotating_handler.setFormatter(Formatter(
			"%(asctime)s %(name)s %(levelname)s: %(message)s [in %(module)s/%(filename)s:%(lineno)d]"))
		
		log = logging.getLogger()
		log.addHandler(rotating_handler)

		from home import app, wok as server

		app.config["CONF_BUILDER"] = self.case_conf_builder
		#app.config["DEMO_MODE"] = self.case_conf.get("demo", dtype=bool)
		
		email_sender_name = self.case_conf.get("email_sender.name", "void")
		email_sender_conf = self.case_conf.get("email_sender.conf")
		if email_sender_conf is not None:
			email_sender_conf = email_sender_conf.to_native()
		else:
			email_sender_conf = {}

		app.config["EMAIL_SENDER"] = (email_sender_name, email_sender_conf)

		#if server_domain is not None:
		#	app.config["SERVER_NAME"] = server_domain

		if server_port == 80:
			domain = server_host
		else:
			domain = "{0}:{1}".format(server_host, server_port)
		
		app.config["VALIDATION_DOMAIN"] = server_domain or domain
		app.config["VALIDATE_SIGNUP"] = self.case_conf.get("validate_signup", False)

		server.run()
