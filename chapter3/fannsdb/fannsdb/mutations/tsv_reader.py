from bgcore import tsv

from mutation import Mutation

class MutationsTsvReader(object):
	_G_COLS = set(["ID", "CHR", "STRAND", "START", "REF", "ALT"])
	_P_COLS = set(["TRANSCRIPT", "PROTEIN", "AA_POS", "AA_REF", "AA_ALT"])
	COLUMNS = _G_COLS | _P_COLS

	_MUT_ATTR = {
		"ID" : "identifier", "CHR" : "chr", "STRAND" : "strand", "START" : "start",
		"REF" : "ref", "ALT" : "alt", "TRANSCRIPT" : "protein",
		"PROTEIN" : "PROTEIN", "AA_REF" : "ref", "AA_ALT" : "alt" }

	_ATTR_TYPE = {
		"START" : int
	}

	def __init__(self, path, coord_type=None, rename_cols=None, separator="\t"):
		self.path = path
		self.coord_type = coord_type
		self.rename_cols = rename_cols or {}
		self.separator = separator
		self.__f = None
		self.line_num = 0

	def __open(self):
		self.__f = tsv.open(self.path)
		self.line_num = 0

	def __close(self):
		if self.__f is not None:
			self.__f.close()
			self.__f = None

	def __readline(self):
		line = self.__f.readline()
		stripped_line = line.rstrip("\n\r")
		self.line_num += 1
		while line.startswith("#") or (len(line) > 0 and len(stripped_line) == 0):
			line = self.__f.readline()
			stripped_line = line.rstrip("\n\r")
			self.line_num += 1

		return line, stripped_line

	def __iter__(self):
		return self

	def next(self):
		if self.__f is None:
			self.__open()
			line, stripped_line = self.__readline()
			self.hdr = {self.rename_cols.get(c, c).upper() : i for i, c in enumerate(stripped_line.split(self.separator))}
			all_cols = set(self.hdr.keys())
			coord_cols = all_cols & self.COLUMNS
			req_gen_headers = len(set(["CHR", "START"]) & coord_cols) == 2 and len(set(["REF", "ALT"]) & coord_cols) >= 1
			req_prot_headers = len(set(["TRANSCRIPT", "PROTEIN"])) >= 1 and "AA_POS" in coord_cols and len(set(["AA_REF", "AA_ALT"]) & coord_cols) >= 1
			if self.coord_type is None: # infer type of coordinates from the columns header
				if req_gen_headers:
					self.coord_type = Mutation.GENOMIC
					columns = all_cols & self._G_COLS
				elif req_prot_headers:
					self.coord_type = Mutation.PROTEIN
					columns = all_cols & self._P_COLS
				else:
					raise Exception("Not possible to infer which kind of coordinates to use from the headers")
			elif self.coord_type == Mutation.GENOMIC:
				columns = all_cols & self._G_COLS
				if not req_gen_headers:
					raise Exception("Missing required headers for genomic coordinates: CHR, START and any of REF or ALT")
			elif self.coord_type == Mutation.PROTEIN:
				columns = all_cols & self._P_COLS
				if not req_prot_headers:
					raise Exception("Missing required headers for proteomic coordinates: any of TRANSCRIPT or PROTEIN and AA_POS and any of AA_REF or AA_ALT")
			else:
				raise Exception("Unknown coordinate type: {}".format(self.coord_type))

			self.columns = [(c, self.hdr[c], self._MUT_ATTR[c], self._ATTR_TYPE.get(c)) for c in columns]

		line, stripped_line = self.__readline()

		if len(line) == 0:
			raise StopIteration

		line = stripped_line
		fields = line.split(self.separator)
		num_fields = len(fields)

		m = Mutation()
		m.coord = self.coord_type
		for col, ix, attr, atype in self.columns:
			if ix < num_fields:
				if atype is not None:
					setattr(m, attr, atype(fields[ix]))
				else:
					setattr(m, attr, fields[ix])

		return m