import numpy

from intogen.io import FileReader, FileWriter

def str_is_nan(text):
	return text in ["-", "NA"] or len(text) == 0

def str_to_int(text):
	if str_is_nan(text):
		raise Exception("Empty/Nan value not allowed for integers")
	else:
		return int(text)

def str_to_float(text):
	if str_is_nan(text):
		return numpy.nan
	else:
		return float(text)

def float_to_str(value):
	if numpy.isnan(value):
		return "-"
	else:
		return str(value)

class MatrixHeader(object):
	def __init__(self, hdr):
		self.columns = hdr
		self.labels_column = None
		self.data_columns = []
		if len(hdr) > 0:
			self.labels_column = hdr[0]
			if len(hdr) > 1:
				self.data_columns = hdr[1:]

	def __repr__(self):
		return ", ".join(self.columns)

class MatrixRow(object):
	def __init__(self, name, values):
		self.name = name
		self.values = values

class MatrixReader(FileReader):
	def __init__(self, obj, dtype=float):
		FileReader.__init__(self, obj)

		self.dtype = dtype

		self.header = None

	def _parser_from_type(self, dtype):
		if dtype == float:
			return str_to_float
		elif dtype == int:
			return str_to_int
		else:
			return str

	def read_header(self):
		if self.header == None:
			line = FileReader.readline(self).rstrip()
			hdr = line.split("\t")
			self.header = MatrixHeader(hdr)

		return self.header

	def __iter__(self):
		parser = self._parser_from_type(self.dtype)

		self.read_header()

		for line in FileReader.__iter__(self):
			line = line.rstrip()

			fields = line.split("\t")
			row_name = fields[0]
			values = [parser(x) for x in fields[1:]]

			yield MatrixRow(row_name, values)

	def __str__(self):
		return str(self.f) + ", dtype=" + str(dtype)

class MatrixWriter(FileWriter):
	def __init__(self, obj, dtype=float):
		FileWriter.__init__(self, obj)

		self.dtype = dtype

	def _value_to_str_func(self, dtype):
		if dtype == float:
			return float_to_str
		else:
			return str

	def write_header(self, header = None):
		if isinstance(header, MatrixHeader):
			FileWriter.write(self, "\t".join(header.columns))
		elif isinstance(header, (list, tuple)):
			FileWriter.write(self, "\t".join(header))
		else:
			raise Exception("Unsupported headers type: {}".format(str(type(header))))
		FileWriter.write(self, "\n")

	def write(self, name, values):
		value_to_str = self._value_to_str_func(self.dtype)

		FileWriter.write(self, name)
		for value in values:
			FileWriter.write(self, "\t")
			FileWriter.write(self, value_to_str(value))
		FileWriter.write(self, "\n")

