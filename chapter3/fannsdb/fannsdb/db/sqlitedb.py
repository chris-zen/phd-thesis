import os
import re
import sqlite3
from datetime import datetime

from fannsdb.db import FannsDb

CHR = ["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
	"11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
	"21", "22", "23", "X", "Y"]

CHR_LIST = CHR[1:23] + CHR[24:]

CHR_INDEX = dict([(c, i) for i, c in enumerate(CHR)])
CHR_INDEX["23"] = CHR_INDEX["X"]
CHR_INDEX["24"] = CHR_INDEX["Y"]

STRANDS = ["+", "-"]

STRAND_INDEX = {
	"+" : 0, "+1" : 0, "1" : 0,
	"-" : 1, "-1" : 1
}

BASES = ["A", "C", "G", "T"]

BASE_INDEX = {"A" : 0, "C" : 1, "G" : 2, "T" : 3}

AA = ["A", "R", "N", "D", "C", "E", "Q", "G", "H", "I", "L", "K", "M", "F", "P", "S", "T", "W", "Y", "V",
	  "U", "O", "B", "Z", "J", "X"]

AA_INDEX = dict([(aa, i) for i, aa in enumerate(AA)])

DATE_FMT = "%Y-%m-%d %H:%M:%S"

DB_VERSION = "01"

ENST = re.compile(r"^ENST[0-9]+$")
ENSP = re.compile(r"^ENSP[0-9]+$")

class FannsSQLiteDb(FannsDb):
	DNA_COORD = "dna"
	PROTEIN_COORD = "protein"

	DNA_FILTER = DNA_COORD
	PROTEIN_FILTER = PROTEIN_COORD

	ALL_FIELDS = set([
		"chr", "start", "ref", "alt", "strand", "transcript",
		"protein", "aa_pos", "aa_ref", "aa_alt"])

	DNA_FIELDS = set(["chr", "start", "ref", "alt", "strand"])
	PROTEIN_FIELDS = set(["protein", "aa_pos", "aa_ref", "aa_alt"])

	ALL_FILTERS = set([
		"chr", "start", "ref", "alt", "strand", "transcript",
		"protein", "aa_pos", "aa_ref", "aa_alt"])

	DNA_FILTERS = set(["chr", "start", "ref", "alt", "strand"])
	DNA_REQ_FILTERS = set(["start"])

	PROTEIN_FILTERS = set(["aa_pos", "aa_ref", "aa_alt"])
	PROTEIN_REQ_FILTERS = set(["aa_pos"])

	def __init__(self, path):
		self.path = path

		self.__conn = None
		
		self.__id_cache = {}
		self.__predictors = None
		self.__predictors_by_id = None
		self.__maps = None
		self.__maps_by_id = None

	def open(self, create=False):
		if not create and not os.path.exists(self.path):
			raise Exception("Database not found: {}".format(self.path))

		self.__conn = sqlite3.connect(self.path)
		self.__conn.row_factory = sqlite3.Row

		c = self.__conn.cursor()

		try:
			c.execute("SELECT db_version FROM meta")
			res = c.fetchone()
			db_version, = res
		except:
			self.create()
			db_version = DB_VERSION

		if db_version != DB_VERSION:
			raise Exception("Database version {} is incompatible, required {}".format(db_version, DB_VERSION))

		self.db_version = db_version

		c.execute("SELECT creation_time FROM meta")
		res = c.fetchone()
		if res is None:
			raise Exception("unexpected error: meta table is empty")

		creation_time, = res

		self.creation_time = datetime.strptime(creation_time, DATE_FMT)

		self.__load_id_cache(c, "transcript")
		self.__load_id_cache(c, "protein")

		c.close()

	def __create_id_table(self, name):
		c = self.__conn.cursor()
		c.executescript("""
			CREATE TABLE IF NOT EXISTS id_{0} (
				{0}_id INTEGER PRIMARY KEY,
				{0}_name TEXT UNIQUE
			);
		""".format(name))
		c.close()

	def __get_id(self, c, var_name, value, read_only=False):
		if value is None:
			return None

		if var_name in self.__id_cache:
			var_cache = self.__id_cache[var_name]
			if value in var_cache:
				return var_cache[value]
		else:
			self.__id_cache[var_name] = {}

		if not read_only:
			c.execute("INSERT INTO id_{0} ({0}_name) VALUES (?)".format(var_name), (value,))
			var_id = c.lastrowid

			self.__id_cache[var_name][value] = var_id

			return var_id

		return -1

	def __load_id_cache(self, c, var_name):
		cache = {}
		for id, name in c.execute("SELECT {0}_id, {0}_name FROM id_{0}".format(var_name)):
			cache[name] = id
		self.__id_cache[var_name] = cache
		
	def create(self):
		c = self.__conn.cursor()

		c.execute("""CREATE TABLE IF NOT EXISTS meta (
			db_version 			TEXT,
			creation_time 		INTEGER,
			initialized			INTEGER DEFAULT 0)""")

		c.execute("INSERT INTO meta (db_version, creation_time) VALUES (?,?)",
			(DB_VERSION, datetime.now().strftime(DATE_FMT)))

		self.__create_id_table("transcript")
		self.__create_id_table("protein")

		c.executescript("""
			CREATE TABLE predictors (
				id 			TEXT PRIMARY KEY,
				type		TEXT,
				source 		TEXT,
				min			REAL,
				max			REAL,
				count 		INTEGER
			);

			CREATE TABLE annotations (
				id 			TEXT PRIMARY KEY,
				type 		TEXT,
				name 		TEXT,
				priority	INTEGER DEFAULT 0
			);

			CREATE TABLE scores (
				id 				INTEGER PRIMARY KEY,
				dna_code 		INTEGER,
				transcript_id	INTEGER,
				prot_code		INTEGER,
				protein_id		INTEGER);

			PRAGMA synchronous=OFF;
		""")

		c.close()

		self.__conn.commit()

	def create_indices(self):
		c = self.__conn.cursor()
		c.executescript("""
			CREATE UNIQUE INDEX IF NOT EXISTS scores_by_dna ON scores (dna_code, transcript_id);
			CREATE INDEX IF NOT EXISTS scores_by_prot ON scores (protein_id, prot_code);
		""")
		c.close()
		self.__conn.commit()

	def drop_indices(self):
		c = self.__conn.cursor()
		c.executescript("""
			DROP INDEX IF EXISTS scores_by_dna;
			DROP INDEX IF EXISTS scores_by_prot;
		""")
		c.close()
		self.__conn.commit()

	def commit(self):
		self.__conn.commit()

	def rollback(self):
		self.__conn.rollback()

	def close(self):
		if self.__conn is not None:
			self.__conn.close()
			self.__conn = None
		
	def __dna_code(self, chr, strand, start, ref, alt):
		pos = CHR_INDEX[chr] << 33 | STRAND_INDEX[strand] << 32 | start << 4 | BASE_INDEX[ref] << 2 | BASE_INDEX[alt]
		return pos

	def __expand_dna_code(self, pos):
		chr = CHR[(pos >> 33) & 0x1F]
		strand = STRANDS[(pos >> 32) & 0x01]
		start = (pos >> 4) & 0x0FFFFFFF
		ref = BASES[(pos >> 2) & 0x03]
		alt = BASES[pos & 0x03]
		return chr, strand, start, ref, alt

	def __protein_code(self, aa_pos, aa_ref, aa_alt):
		if aa_pos is None:
			aa_pos = 0
		pos = aa_pos << 10 | AA_INDEX[aa_ref] << 5 | AA_INDEX[aa_alt]
		return pos

	def __expand_prot_code(self, pos):
		aa_pos = pos >> 10
		ref = (pos >> 5) & 0x1F
		alt = pos & 0x1F
		return aa_pos, AA[ref], AA[alt]

	def is_initialized(self):
		r = [r for r in self.__conn.execute("SELECT initialized FROM meta")]
		assert len(r) <= 1
		return len(r) == 1 and r[0][0] != 0

	def set_initialized(self, init=True):
		self.__conn.execute("UPDATE meta SET initialized=?", (1 if init else 0, ))

	@property
	def metadata(self):
		r = [r for r in self.__conn.execute("SELECT * FROM meta")]
		assert len(r) <= 1
		return r[0] if len(r) == 1 else {}

	def add_predictor(self, id, type, source=None):
		if isinstance(source, basestring):
			source = [source]

		c = self.__conn.cursor()
		try:
			c.execute("INSERT INTO predictors (id, type) VALUES (?,?)", (id, type))
			if source is not None:
				c.execute("UPDATE predictors SET source=? WHERE id=?", (",".join(source), id))
			c.execute("ALTER TABLE scores ADD COLUMN {} REAL".format(id))
			self.__predictors = None
		except sqlite3.IntegrityError:
			pass
		finally:
			c.close()

	def __cache_predictors(self):
		self.__predictors = []
		self.__predictors_by_id = {}
		for row in self.__conn.execute("SELECT * FROM predictors"):
			a = dict(id=row["id"], type=row["type"], source=row["source"],
						min=row["min"], max=row["max"], count=row["count"])
			self.__predictors += [a]
			self.__predictors_by_id[row["id"]] = a

	def predictors(self, id=None, type=None):
		if self.__predictors is None:
			self.__cache_predictors()
		if id is None and type is None:
			return self.__predictors
		elif id is None and type is not None:
			return [ann for ann in self.__predictors if ann["type"] == type]
		elif id is not None and type is None:
			return self.__predictors_by_id[id] if id in self.__predictors_by_id else None
		elif id is not None and type is not None:
			ann = self.__predictors_by_id.get("id")
			return ann if ann is not None and ann["type"] == type else None

	def update_predictors(self, predictors=None):
		c = self.__conn.cursor()

		if predictors is None:
			predictors = self.predictors()
		elif isinstance(predictors, basestring):
			predictors = [self.predictors(id=predictors)]
		else:
			predictors = [self.predictors(id=p) for p in predictors]

		sb1 = []
		for predictor in predictors:
			pid = predictor["id"]
			sb1 += ["MIN({0}), MAX({0}), COUNT({0})".format(pid)]

		sql = "SELECT " + ", ".join(sb1) + " FROM scores"
		c.execute(sql)
		r = c.fetchone()

		for i, predictor in enumerate(predictors):
			j = i * 3
			c.execute("UPDATE predictors SET min=?, max=?, count=? WHERE id=?", (r[j], r[j + 1], r[j + 2], predictor["id"]))

		self.__predictors = None
		c.close()

	def __cache_maps(self):
		self.__maps = []
		self.__maps_by_id = {}
		for row in self.__conn.execute("SELECT * FROM annotations"):
			a = dict(id=row["id"], type=row["type"], name=row["name"], priority=row["priority"])
			self.__maps += [a]
			self.__maps_by_id[row["id"]] = a

	def add_map(self, id, name, type, priority=0):
		c = self.__conn.cursor()
		
		try:
			c.execute("INSERT INTO annotations (id, type, name, priority) VALUES (?,?,?,?)",
						(id, type, name, priority))

		except sqlite3.IntegrityError:
			c.execute("SELECT type FROM annotations WHERE id=?", (id, ))
			prev_type = c.fetchone()[0]
			if prev_type != type:
				c.execute("DROP TABLE ann_{}".format(id))
			c.execute("UPDATE annotations SET type=?, name=?", (type, name))

		c.execute("""
			CREATE TABLE IF NOT EXISTS ann_{id} (
					{type}_id 	INTEGER,
					ann_{id}	TEXT,

					PRIMARY KEY ({type}_id, ann_{id}))""".format(id=id, type=type))

		c.execute("CREATE INDEX ann_in_{id} ON ann_{id} (ann_{id})".format(id=id))

		self.__maps = self.__maps_by_id = None

		c.close()

	def add_map_item(self, id, source, value):
		c = self.__conn.cursor()
		try:
			type = self.maps(id=id)["type"]
			source_id = self.__get_id(c, type, source)
			c.execute("INSERT INTO ann_{id} ({type}_id, ann_{id}) VALUES (?,?)".format(id=id, type=type), (source_id, value))
		except sqlite3.IntegrityError:
			pass
		finally:
			c.close()

	def remove_map(self, id):
		c = self.__conn.cursor()
		try:
			c.execute("DELETE FROM annotations WHERE id=?", (id, ))
			c.execute("DROP TABLE IF EXISTS ann_{}".format(id))
		except:
			pass
		finally:
			c.close()

	def maps(self, id=None, type=None):
		if self.__maps is None:
			self.__cache_maps()
		if id is None and type is None:
			return self.__maps
		elif id is None and type is not None:
			return [m for m in self.__maps if m["type"] == type]
		elif id is not None and type is None:
			return self.__maps_by_id[id] if id in self.__maps_by_id else None
		elif id is not None and type is not None:
			m = self.__maps_by_id.get("id")
			return m if m is not None and m["type"] == type else None

	def __annotation_to_transcripts(self, name):
		c = self.__conn.cursor()
		transcripts = []
		c.execute("""
			SELECT id, type FROM annotations
			WHERE type = '{}' AND priority > 0
			ORDER BY priority""".format(self.TRANSCRIPT_ANN_TYPE))
		for ann_id, ann_type in c.fetchall():
			c.execute("""
				SELECT {type}_id FROM ann_{id}
				WHERE ann_{id} = ?""".format(id=ann_id, type=ann_type), (name, ))
			transcripts = [row[0] for row in c.fetchall()]
			if len(transcripts) > 0:
				break
		c.close()
		return transcripts

	def __annotation_to_proteins(self, name):
		c = self.__conn.cursor()
		proteins = []
		c.execute("""
			SELECT id, type FROM annotations
			WHERE type = '{}' AND priority > 0
			ORDER BY priority""".format(self.PROTEIN_ANN_TYPE))
		for ann_id, ann_type in c.fetchall():
			c.execute("""
				SELECT {type}_id FROM ann_{id}
				WHERE ann_{id} = ?""".format(id=ann_id, type=ann_type), (name, ))
			proteins = [row[0] for row in c.fetchall()]
			if len(proteins) > 0:
				break
		c.close()
		return proteins

	def add_snv(self, chr, strand, start, ref, alt, transcript=None,
				protein=None, aa_pos=None, aa_ref=None, aa_alt=None,
				scores=None):

		c = self.__conn.cursor()
		try:
			if not (chr in CHR_INDEX and strand in STRAND_INDEX and ref in BASE_INDEX and alt in BASE_INDEX\
					and aa_ref in AA_INDEX and aa_alt in AA_INDEX):

				raise Exception("Wrong chr/strand/ref/alt/prot_ref/prot_alt: {} {} {} {} {} {}".format(chr, strand, ref, alt, aa_ref, aa_alt))

			transcript_id = self.__get_id(c, "transcript", transcript)
			protein_id = self.__get_id(c, "protein", protein)
			
			dna_code = self.__dna_code(chr, strand, start, ref, alt)
			prot_code = self.__protein_code(aa_pos, aa_ref, aa_alt)

			scores_keys = sorted(scores.keys())
			sql = ["INSERT INTO scores (dna_code, transcript_id, prot_code, protein_id"]
			if len(scores) > 0:
					sql += [", ", ", ".join(scores_keys)]
			sql += [") VALUES (?,?,?,?"]
			if len(scores) > 0:
				sql += [",?"] * len(scores)
			sql += [")"]

			params = [dna_code, transcript_id, prot_code, protein_id]
			if len(scores) > 0:
				params += [scores[k] for k in scores_keys]

			c.execute("".join(sql), tuple(params))

			return c.lastrowid

		except sqlite3.IntegrityError:
			#pass
			raise Exception("SNV already added: {} {} {} {} {}".format(chr, strand, start, ref, alt))
		except:
			raise
		finally:
			c.close()

		return None

	def snvs(self):
		c = self.__conn.cursor()
		for row in c.execute("SELECT DISTINCT id, dna_code FROM scores"):
			chr, strand, start, ref, alt = self.__expand_dna_code(row["dna_code"])
			yield dict(id=row["id"], chr=chr, strand=strand, start=start, ref=ref, alt=alt)
		c.close()

	def __transcript_ids(self, transcripts):
		if transcripts is None:
			return []

		if not isinstance(transcripts, list):
			transcripts = [transcripts]

		ids = set()
		for transcript in transcripts:
			if not transcript.startswith("ENST"):
				ids.update(self.__annotation_to_transcripts(transcript))
				continue

			#OPTIMIZATION c = self.__conn.cursor()
			# we don't need a cursor if read_only=True
			transcript_id = self.__get_id(None, "transcript", transcript, read_only=True)
			#c.close()
			#return [transcript_id] if transcript_id != -1 else []
			ids.add(transcript_id)

		return ids

	def __protein_ids(self, proteins):
		if proteins is None:
			return []

		if not isinstance(proteins, list):
			proteins = [proteins]

		ids = set()
		for protein in proteins:
			if not protein.startswith("ENSP"):
				ids.update(self.__annotation_to_proteins(protein))
				continue

			#OPTIMIZATION c = self.__conn.cursor()
			# we don't need a cursor if read_only=True
			protein_id = self.__get_id(None, "protein", protein, read_only=True)
			#c.close()
			#return [protein_id] if protein_id != -1 else []
			ids.add(protein_id)

		return list(ids)

	def __as_list(self, value):
		if isinstance(value, list):
			return value
		else:
			return [value]

	def __transcripts_sql(self, fields=None, predictors=None, annotations=None, **kwargs):
		"""
		Returns the SQL query for scores
		:param fields: The required fields.
		:param predictors: the list of predictors to select
		:param annotations: the list of annotations to join
		:param **kwargs: chr, start, ref, alt, strand, transcript_id, protein_id, aa_pos, aa_ref, aa_alt
		:return: The SQL query
		"""

		if fields is None:
			fields = self.ALL_FIELDS
		else:
			if fields > self.ALL_FIELDS:
				raise Exception("Invalid select fields: {}".format(fields - self.ALL_FIELDS))

		if self.__predictors is None:
			self.__cache_predictors()

		predictors = [pred_id for pred_id in (predictors or []) if pred_id in self.__predictors_by_id]

		if self.__maps is None:
			self.__cache_maps()

		annotations = [ann_id for ann_id in (annotations or []) if ann_id in self.__maps_by_id]

		ann_types = set([self.__maps_by_id[ann_id]["type"] for ann_id in annotations])

		select_dna_code = len(fields & self.DNA_FIELDS) > 0
		select_prot_code = len(fields & self.PROTEIN_FIELDS) > 0
		select_transcript_name = "transcript" in fields
		select_protein_name = "protein" in fields

		#join_protein_name = "protein_id" in kwargs or self.PROTEIN_ANN_TYPE in ann_types
		#join_transcript_name = "transcript_id" in kwargs

		# select coordinates

		sql = ["SELECT id"]
		if select_dna_code:
			sql += [", dna_code"]
		if select_prot_code:
			sql += [", prot_code"]
		if select_transcript_name:
			sql += [", transcript_name"]
		if select_protein_name:
			sql += [", protein_name"]

		# select annotations

		sql += [", ann_{}".format(ann_id) for ann_id in annotations]

		# select predictors

		sql += [", {}".format(p) for p in predictors]

		# from

		sql += [" FROM scores s"]

		# join coordinates

		if select_transcript_name:
			sql += [" JOIN id_transcript t ON (s.transcript_id = t.transcript_id)"]
		if select_protein_name:
			sql += [" JOIN id_protein p ON (s.protein_id = p.protein_id)"]

		# join annotations

		for i, ann_id in enumerate(annotations):
			ann_type = self.__maps_by_id[ann_id]["type"]
			sql += [" LEFT JOIN ann_{ann} {i} ON (s.{type}_id = {i}.{type}_id)".format(
						i="a{}".format(i), ann=ann_id, type=ann_type)]

		params = []
		if len(kwargs) > 0:
			filters = {}
			for k, v in kwargs.items():
				if k not in self.ALL_FILTERS:
					raise Exception("Unknown filter: {}".format(k))

				if k == "transcript":
					k = "s.transcript_id"
					v = list(self.__transcript_ids(v))
					if len(v) == 0:
						return None, None

				elif k == "protein":
					k = "s.protein_id"
					v = list(self.__protein_ids(v))
					if len(v) == 0:
						return None, None

				if v is None:
					continue

				if isinstance(v, list):
					v_len = len(v)
					if v_len == 0 or (v_len == 1 and v[0] is None):
						continue

					if v_len == 1:
						v = v[0]

				filters[k] = v

			keys = set(filters.keys())
			
			dna_code_fields = keys & self.DNA_FILTERS
			if len(dna_code_fields) > 0:
				missing_dna_code_fields = self.DNA_FILTERS - dna_code_fields
				if self.DNA_REQ_FILTERS <= missing_dna_code_fields:
					raise Exception("Missing required filters: {}".format(
						self.DNA_REQ_FILTERS & missing_dna_code_fields))

				for field in missing_dna_code_fields:
					if field == "chr":
						filters["chr"] = CHR_LIST
					elif field == "ref":
						filters["ref"] = BASES
					elif field == "alt":
						filters["alt"] = BASES
					elif field == "strand":
						filters["strand"] = STRANDS

				start = filters["start"]
				dna_codes = []
				for chrom in self.__as_list(filters["chr"]):
					for ref in self.__as_list(filters["ref"]):
						for alt in self.__as_list(filters["alt"]):
							for strand in self.__as_list(filters["strand"]):
								try:
									dna_codes += [self.__dna_code(chrom, strand, start, ref, alt)]
								except:
									raise Exception("Wrong DNA coordinate: {}:{}:{}:{}>{}".format(chrom, strand, start, ref, alt))
									#pass # DANGEROUS pass

				for key in self.DNA_FILTERS:
					del filters[key]
				
				num_dna_codes = len(dna_codes)
				if num_dna_codes == 1:
					filters["dna_code"] = dna_codes[0]
				elif num_dna_codes > 1:
					filters["dna_code"] = dna_codes

			protein_code_fields = keys & self.PROTEIN_FILTERS
			if len(protein_code_fields) > 0:
				missing_protein_code_fields = self.PROTEIN_FILTERS - protein_code_fields
				if self.PROTEIN_REQ_FILTERS <= missing_protein_code_fields:
					raise Exception("Missing required filters: {}".format(
						self.PROTEIN_REQ_FILTERS & missing_protein_code_fields))

				for field in missing_protein_code_fields:
					if field == "aa_ref":
						filters["aa_ref"] = AA
					elif field == "aa_alt":
						filters["aa_alt"] = AA

				aa_pos = filters["aa_pos"]
				protein_codes = []
				for aa_ref in self.__as_list(filters["aa_ref"]):
					for aa_alt in self.__as_list(filters["aa_alt"]):
						protein_codes += [self.__protein_code(aa_pos, aa_ref, aa_alt)]

				for key in self.PROTEIN_FILTERS:
					if key in filters:
						del filters[key]
				
				num_protein_codes = len(protein_codes)
				if num_protein_codes == 1:
					filters["prot_code"] = protein_codes[0]
				elif num_protein_codes > 1:
					filters["prot_code"] = protein_codes
			
			sql += [" WHERE"]
			first_condition = True
			for k, v in filters.items():
				if first_condition:
					first_condition = False
				else:
					sql += [" AND"]

				if isinstance(v, list):
					sql += [" {} IN ({})".format(k, ",".join(["?"] * len(v)))]
					params += v
				else:
					sql += [" {} = ?".format(k)]
					params += [v]

		return "".join(sql), params

	def query_scores(self, fields=None, predictors=None, annotations=None, **filters):
		"""
		:param fields: The fields to retrieve
		:param predictors: the list of predictors to select
		:param annotations: the list of annotations to join
		:param filters: chr, start, end, ref, alt, strand, transcript, protein, aa_pos, aa_ref, aa_alt
		"""

		fields = set(fields) if fields is not None else self.ALL_FIELDS

		select_dna_code = len(fields & self.DNA_FIELDS) > 0
		select_prot_code = len(fields & self.PROTEIN_FIELDS) > 0
		select_transcript_name = "transcript" in fields
		select_protein_name = select_prot_code or "protein" in fields

		sql, params = self.__transcripts_sql(fields=fields, predictors=predictors, annotations=annotations,
											**filters)

		if sql is None:
			return

		c = self.__conn.cursor()
		try:
			c.execute(sql, params)
			for row in c:
				data = dict(id=row["id"])
				if select_dna_code:
					chr, strand, start, ref, alt = self.__expand_dna_code(row["dna_code"])
					data.update(dict(chr=chr, strand=strand, start=start, ref=ref, alt=alt))

				if select_prot_code:
					aa_pos, aa_ref, aa_alt = self.__expand_prot_code(row["prot_code"])
					data.update(dict(aa_pos=aa_pos, aa_ref=aa_ref, aa_alt=aa_alt))

				if select_transcript_name:
					data["transcript"]=row["transcript_name"]

				if select_protein_name:
					data["protein"]=row["protein_name"]

				scores = {}
				if predictors is not None:
					for predictor in predictors:
						scores[predictor] = row[str(predictor)]
				data["scores"] = scores

				ann = {}
				if annotations is not None:
					for ann_id in annotations:
						ann[ann_id] = row["ann_{}".format(ann_id)]
				data["annotations"] = ann

				yield data
		finally:
			c.close()

	def update_scores(self, rowid, scores):
		"""
		:param rowid: The row id
		:param scores: The scores to be updated
		"""

		if len(scores) == 0:
			return

		c = self.__conn.cursor()

		sql = ["UPDATE scores SET "]
		values = []
		for i, (predictor_name, score) in enumerate(scores.items()):
			if i != 0:
				sql += [", "]
			sql += ["{}=?".format(predictor_name)]
			values += [score]
		sql += [" WHERE id = ?"]

		c.execute("".join(sql), tuple(values + [rowid]))
		c.close()