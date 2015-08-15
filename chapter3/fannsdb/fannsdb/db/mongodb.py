from bson.son import SON
from pymongo import MongoClient
import pymongo.uri_parser

from fannsdb.db import FannsDb

from fannsdb.columns import COORD_COLUMNS

class FannsMongoDb(FannsDb):

	FIELD_TO_KEY = dict(
		chr="g.c", start="g.s", ref="g.r", alt="g.a", transcript="g.t", strand="g.d",
		protein="p.n", aa_pos="p.p", aa_ref="p.r", aa_alt="p.a")

	KEY_TO_FIELD = dict([(k, f) for f, k in FIELD_TO_KEY.items()])

	IDPREFIX = {
		FannsDb.TRANSCRIPT_MAP_TYPE : "ENST",
		FannsDb.PROTEIN_MAP_TYPE : "ENSP"
	}

	def __init__(self, *args, **kwargs):

		uri = kwargs.pop("uri", None)
		conn = kwargs.pop("conn", None)
		db = kwargs.pop("db", None)
		db_name = kwargs.pop("db_name", "fanns")

		if db is not None:
			self._conn = db.connection
			self._db = db

		elif conn is not None:
			self._conn = conn
			self._db = db if db is not None else self._conn[db_name]

		elif uri is not None:
			parsed_uri = pymongo.uri_parser.parse_uri(uri)
			db_name = parsed_uri.get("database", db_name)
			self._conn = MongoClient(uri)
			self._db = self._conn[db_name]

		else:
			self._conn = MongoClient(*args, **kwargs)
			self._db = db if db is not None else self._conn[db_name]

		self.__maps = None
		self.__maps_fast = None
		self.__maps_by_id = None

		self.__xrefs_cache = {}

	def open(self, create=False):
		pass

	def create(self):
		pass

	def create_indices(self):
		pass #self._db.scores.ensure_index([])

	def drop_indices(self):
		#self._db.drop_index("genome")
		#self._db.drop_index("protein")
		pass

	def commit(self):
		pass

	def rollback(self):
		pass

	def close(self):
		pass

	def is_initialized(self):
		meta = self._db.meta.find_one()
		if meta is None:
			return False
		return meta.get("initialized", False)

	def set_initialized(self, init=True):
		self._db.meta.update({}, {"$set" : {"initialized" : True}}, upsert=True)

	@property
	def metadata(self):
		return self._db.meta.find_one() or {}

	def add_predictor(self, id, type, source=None):
		raise NotImplemented()

	def predictors(self, id=None, type=None):
		raise NotImplemented()

	def update_predictors(self, predictors=None):
		raise NotImplemented()

	def __load_maps_cache(self):
		self.__maps = []
		self.__maps_fast = {self.PROTEIN_MAP_TYPE : [], self.TRANSCRIPT_MAP_TYPE : []}
		self.__maps_by_id = {}

		for map_info in self._db.maps.find(sort=[("priority", 1)]):
			map_info["id"] = map_info["_id"]
			del map_info["_id"]
			self.__maps += [map_info]
			if map_info["priority"] > 0:
				self.__maps_fast[map_info["type"]] += [map_info]
			self.__maps_by_id[map_info["id"]] = map_info

	def __clean_map_cache(self, map_id):
		self.__maps = self.__maps_fast = self.__maps_by_id = None

		for mid, name in self.__xrefs_cache.keys():
			if mid == map_id:
				del self.__xrefs_cache[(mid, name)]

	def add_map(self, map_id, name, type, priority=0):
		replace = self._db.maps.find_one({"_id" : map_id}) != None

		d = SON([("_id", map_id), ("name", name), ("type", type), ("priority", priority)])

		self._db.maps.update({"_id" : map_id}, d, upsert=True)

		if replace:
			self._db.maps[map_id].drop()

		self._db.maps.ensure_index([("priority", 1)])
		self._db.maps[map_id].ensure_index([("x", 1)])

		self.__clean_map_cache(map_id)

	def add_map_item(self, map_id, source, value):
		type = self.maps(id=map_id)["type"]
		self._db.maps[map_id].update({"_id" : value}, { "$addToSet" : {"x" : source}}, upsert=True)

	def remove_map(self, map_id):
		self._db.maps.remove({"_id" : map_id})
		self._db.maps[map_id].drop()

		self.__clean_map_cache(map_id)

	def maps(self, id=None, type=None):
		if self.__maps is None:
			self.__load_maps_cache()
		if id is None and type is None:
			return self.__maps
		elif id is None and type is not None:
			return [m for m in self.__maps if m["type"] == type]
		elif id is not None and type is None:
			return self.__maps_by_id[id] if id in self.__maps_by_id else None
		elif id is not None and type is not None:
			m = self.__maps_by_id.get("id")
			return m if m is not None and m["type"] == type else None

	def map_xref(self, type, xref):
		"""
		xref to ensembl
		"""
		if self.__maps is None:
			self.__load_maps_cache()

		ids = []
		for m in self.__maps_fast[type]:
			x = self._db.maps[m["id"]].find_one({"_id" : xref}, {"x" : 1}) # TODO cache map items
			if x is not None and len(x) > 0:
				ids = x["x"]
				break
		return ids

	def map_xrefs(self, type, xrefs):
		"""
		xref to ensembl
		"""
		if xrefs is None:
			return []

		prefix = self.IDPREFIX[type]
		if isinstance(xrefs, basestring):
			if xrefs.startswith(prefix):
				return [xrefs]
			else:
				return self.map_xref(type, xrefs)
		elif isinstance(xrefs, list):
			ids = set()
			for xref in xrefs:
				if xrefs.startswith(prefix):
					ids.add(xref)
				else:
					ids.update(self.map_xref(type, xref))
			return list(ids)

	def get_xrefs(self, map_id, name):
		"""
		ensembl to xrefs
		"""
		key = (map_id, name)
		if key in self.__xrefs_cache:
			return self.__xrefs_cache[key]

		xrefs = [d["_id"] for d in self._db.maps[map_id].find({"x" : name}, {"_id" : 1})]
		num_xrefs = len(xrefs)
		if num_xrefs == 0:
			xrefs = None
		elif num_xrefs == 1:
			xrefs = xrefs[0]

		self.__xrefs_cache[key] = xrefs

		return xrefs

	def __query_from_filters(self, filters):
	
		query = dict([(self.FIELD_TO_KEY[field], value) for field, value in filters.items() if field in self.FIELD_TO_KEY and value is not None])

		if "g.t" in query:
			ids = self.map_xrefs(self.TRANSCRIPT_MAP_TYPE, query["g.t"])
			num_ids = len(ids)
			if num_ids == 0:
				return None
			elif num_ids == 1:
				query["g.t"] = ids[0]
			else:
				query["g.t"] = {"$in" : ids}

		if "p.n" in query:
			ids = self.map_xrefs(self.PROTEIN_MAP_TYPE, query["p.n"])
			num_ids = len(ids)
			if num_ids == 0:
				return None
			elif num_ids == 1:
				query["p.n"] = ids[0]
			else:
				query["p.n"] = {"$in" : ids}

		return query

	def query_scores(self, fields=None, predictors=None, maps=None, **filters):

		if self.__maps is None:
			self.__load_maps_cache()

		predictors = [] if predictors is None else predictors
		
		fields = fields or [c.lower() for c in COORD_COLUMNS]
		fields = [(self.FIELD_TO_KEY[field], 1) for field in fields if field in self.FIELD_TO_KEY]
		fields += [("s." + pred, 1) for pred in predictors]
		fields = dict(fields)

		query = self.__query_from_filters(filters)
		if query is None:
			return

		for d in self._db.scores.find(query, fields):
			r = [("id", d["_id"])]
			if "g" in d:
				r += [(self.KEY_TO_FIELD["g." + k], v) for k, v in d["g"].items()]
			if "p" in d:
				r += [(self.KEY_TO_FIELD["p." + k], v) for k, v in d["p"].items()]
			r = dict(r)

			if predictors is not None:
				s = d.get("s") or {}
				r["scores"] = dict([(p, s[p] if p in s else None) for p in predictors])

			if maps is not None:
				r["xrefs"] = xrefs = dict()
				for map_id in maps:
					if map_id not in self.__maps_by_id:
						continue
					map_info = self.__maps_by_id[map_id]
					if map_info["type"] == self.TRANSCRIPT_MAP_TYPE:
						src_id = d["g"]["t"]
					else:
						src_id = d["p"]["n"]

					xrefs[map_id] = self.get_xrefs(map_id, src_id)

			yield r

	def update_scores(self, scores, id=None, **filters):
		if id is not None:
			query = {"_id" : id}
		else:
			query = self.__query_from_filters(filters)
			if query is None:
				return
		
		scores = dict([("s." + key, value) for key, value in scores.items()])
		
		self._db.scores.update(query, {"$set" : scores}, multi=True)
		
