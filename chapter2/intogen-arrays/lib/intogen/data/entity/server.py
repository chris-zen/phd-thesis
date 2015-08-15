import os.path
import os
import json
import uuid

try:
	from lxml import etree
except ImportError:
	try:
		# Python 2.5
		import xml.etree.cElementTree as etree
	except ImportError:
		try:
			# Python 2.5+
			import xml.etree.ElementTree as etree
		except ImportError:
			try:
				# normal cElementTree install
				import cElementTree as etree
			except ImportError:
				try:
					# normal ElementTree install
					import elementtree.ElementTree as etree
				except ImportError:
					import sys
					sys.stderr.write("Failed to import ElementTree from any known place\n")
					raise

from wok import logger
from wok.element import DataElement, DataElementJsonEncoder, \
						dataelement_from_xml, dataelement_from_json_path

class NotUnique(Exception):
	pass

class EntityServer(object):
	"""
	Instantiates the correspondig entity manager.

	* Configuration parameters:

	- The ones required by the entity manager implementation
	"""

	def __init__(self, conf):
		self.sources = conf

	def manager(self):
		return FileEntityManager(self.sources)

	def close(self):
		pass

class FileEntityManager(object):
	"""
	Manages entities on a file system.

	* Configuration parameters:

	- work_path: Working path for files

	"""

	def __init__(self, conf):

		if "sources" in conf:
			self.sources = conf["sources"]
		else:
			self.sources = DataElement()

		self.log = logger.get_logger(conf.get("log"), name = "em_file")
	
	def _entity_meta(self, etype):
		tpath = etype.split(".")

		sources = self.sources
		base_path = sources.get("__default.path", None)
		format = sources.get("__default.format", "json")

		i = 0
		while i < len(tpath):
			#self.log.debug("i=%i, %s | %s" % (i, "/".join(tpath[0:i+1]), "/".join(tpath)))
			#self.log.debug("%s in %s" % (tpath[i], sources))
			if tpath[i] not in sources:
				#self.log.debug("%s not in sources" % tpath[i])
				break

			sources = sources[tpath[i]]
			base_path = sources.get("__default.path", base_path)
			format = sources.get("__default.format", format)
			base_path = sources.get("path", base_path)
			format = sources.get("format", format)
			
			i += 1

		#self.log.debug(">>> %s : %s" % (base_path, format))

		if base_path is None:
			raise Exception("Path for entity type '%s' not found in configuration section 'entities.sources'" % etype)
		
		base_path = os.path.join(base_path, "/".join(tpath[i:]))

		return (base_path, format)

	def find(self, eid, etype):
		coll_path, ext = self._entity_meta(etype)
		path = os.path.join(coll_path, "%s.%s" % (eid, ext))
		if not os.path.exists(path):
			self.log.error("%s with id %s not found at %s" % (etype, eid, path))
			return None

		if ext == "xml":
			root = etree.parse(path).getroot()
			data = dataelement_from_xml(root)
		else:
			data = dataelement_from_json_path(path)

		data["__doc_path"] = path
		data["__type"] = etype
		return data
		
	def find_ids(self, etype):
		coll_path, ext = self._entity_meta(etype)
		ids = []
		if not os.path.exists(coll_path):
			return ids
		
		for filename in os.listdir(coll_path):
			end = filename.rfind(ext) - 1
			if end > 0:
				ids.append(filename[0:end])
		return ids
	
	def iter_all(self, etype, eids = []):
		eids = set(eids)
		coll_path, ext = self._entity_meta(etype)
		if not os.path.exists(coll_path):
			return

		for filename in os.listdir(coll_path):
			path = os.path.join(coll_path, filename)
			if not path.endswith("." + ext):
				continue

			try:
				if ext == "xml":
					root = etree.parse(path).getroot()
					data = dataelement_from_xml(root)
				else:
					data = dataelement_from_json_path(path)
			except:
				self.log.error("Error loading and parsing document {}".format(path))
				raise
			
			if len(eids) == 0 or data["id"] in eids:
				data["__doc_path"] = path
				data["__type"] = etype
				yield data

	def persist(self, e, etype = None):
		if "id" not in e:
			e["id"] = str(uuid.uuid4())
			
		eid = e["id"]
		
		if etype is None:
			if "__type" not in e:
				raise Exception("Unknown entity type: %s" % eid)
				
			etype = e["__type"]

		if "__type" in e:
			del e["__type"]
		if "__doc_path" in e:
			del e["__doc_path"]
			
		coll_path, ext = self._entity_meta(etype)
		if not os.path.exists(coll_path):
			try:
				os.makedirs(coll_path)
			except:
				if not os.path.exists(coll_path):
					raise

		f = open(os.path.join(coll_path, "%s.%s" % (eid, ext)), "w")
		json.dump(e, f, sort_keys=True, indent=4, cls=DataElementJsonEncoder)
		f.close()

	def group_ids(self, fields, etype, eids = [], unique = False):
		index = {}
		for e in self.iter_all(etype, eids):
			k = []
			for field in fields:
				k += [e.get(field, None)]
			key = tuple(k)
			if key not in index:
				index[key] = [e["id"]]
			else:
				index[key] += [e["id"]]
				
		if unique:
			for k, v in index.iteritems():
				if len(v) > 1:
					raise NotUnique("Non unique {} group found for key ({}). Colliding id's: {}".format(
							etype, ", ".join([x if x is not None else "" for x in k]), ", ".join(v)))

		return index

	def ensure_collection_exists(self, coll_name):
		coll_path = self._entity_meta(coll_name)[0]
		if not os.path.exists(coll_path):
			os.makedirs(coll_path)

	def close(self):
		pass

