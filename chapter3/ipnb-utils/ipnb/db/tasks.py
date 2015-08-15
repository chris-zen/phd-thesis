import sys
import logging
import socket
from datetime import datetime as dt

from ipnb.db.utils import mongodb_from_uri

class Task(object):
	def __init__(self, uri, name, item=None):
		self.name = name
		self.item = item
		self.id = {"name" : self.name, "item" : self.item}
		self.title = "{}/{}".format(name, item) if item is not None else name

		try:
			self.hostname = socket.gethostname()
		except:
			self.hostname = "unknown"

		self.logger = logging.getLogger(self.title)
		for h in self.logger.handlers:
			self.logger.removeHandler(h)
		h = logging.StreamHandler(sys.stdout)
		h.setFormatter(logging.Formatter("%(asctime)s %(name)-10s [%(levelname)-7s] %(message)s", "%Y-%m-%d %H:%M:%S"))
		self.logger.addHandler(h)
		self.logger.setLevel(logging.INFO)
		self.logger.propagate = False

		self.db = mongodb_from_uri(uri, db_name="ipnb")

		self.db.tasks.update(self.id, {"$set" : {"state" : "running",
												 "started" : dt.now(),
												 "host" : self.hostname}}, upsert=True)

		self.logger.info("Task {} started on host {}".format(self.title, self.hostname))

	# deprecated
	def log(self, level, msg):
		ts = dt.now()
		self.db.tasks.update(self.id, {"$push" : {"logs" : { "t" : ts, "l" : level, "m" : msg}}})
		print("{} {} {}".format(ts, level.upper(), msg))

	# deprecated
	def info(self, msg):
		self.log("info", msg)

	# deprecated
	def debug(self, msg):
		self.log("debug", msg)

	def progress(self, count=None, text=None):
		s, u = [("progress.updated", dt.now())], []
		if count is not None:
			s += [("progress.count", count)]
		else:
			u += [("progress.count", "")]
		if text is not None:
			s += [("progress.text", text)]
		else:
			u += [("progress.text", "")]
		upd = {"$set" : dict(s)}
		if len(u) > 0:
			upd["$unset"] = dict(u)
		self.db.tasks.update(self.id, upd)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		if exc_type is None:
			self.finished()
		else:
			import traceback
			self.error(exception=repr(exc_val), traceback=traceback.format_tb(exc_tb))

		return False

	def metadata(self, **kwargs):
		upd = [("meta.{}".format(k), v) for k, v in kwargs.items()]
		self.db.tasks.update(self.id, {"$set" : dict(upd)})

	def finished(self, **kwargs):
		upd = [("state", "finished"), ("finished", dt.now())]
		upd += [("meta.{}".format(k), v) for k, v in kwargs.items()]
		self.db.tasks.update(self.id, {"$set" : dict(upd), "$unset" : {"progress" : ""}})

	def error(self, **kwargs):
		upd = []
		if "exception" in kwargs:
			upd += [("exception", kwargs.pop("exception"))]
		if "traceback" in kwargs:
			upd += [("traceback", kwargs.pop("traceback"))]
		upd += [("state", "failed"), ("failed", dt.now())]
		upd += [("meta.{}".format(k), v) for k, v in kwargs.items()]
		self.db.tasks.update(self.id, {"$set" : dict(upd), "$unset" : {"progress" : ""}})
