class FileReader(object):
	def __init__(self, inp):
		if isinstance(inp, str) or isinstance(inp, unicode):
			if inp.endswith(".gz"):
				import gzip
				self.f = gzip.open(inp, "r")
			elif inp.endswith(".bz2"):
				import bz2
				self.f = bz2.BZ2File(inp)
			else:
				if inp == "-":
					import sys
					self.f = sys.stdin
				else:
					self.f = open(inp, "r")
		elif isinstance(inp, FileReader):
			self.f = inp.f
		else:
			self.f = inp

	def __iter__(self):
		for line in self.f:
			yield line

	def next(self):
		return self.f.next()

	def read(self, size = None):
		if size is None:
			return self.f.read()
		else:
			return self.f.read(size)

	def readline(self, size = None):
		if size is None:
			return self.f.readline()
		else:
			return self.f.readline(size)

	def close(self):
		import sys
		if self.f != sys.stdin:
			self.f.close()

class FileWriter(object):
	def __init__(self, out):
		if isinstance(out, str) or isinstance(out, unicode):
			if out.endswith(".gz"):
				import gzip
				self.f = gzip.open(out, "w")
			elif out.endswith(".bz2"):
				import bz2
				self.f = bz2.BZ2File(out)
			else:
				if out == "-":
					import sys
					self.f = sys.stdout
				else:
					self.f = open(out, "w")
		elif isinstance(out, FileWriter):
			self.f = out.f
		else:
			self.f = out

	def write(self, data):
		self.f.write(data)

	def flush(self):
		self.f.flush()
		
	def close(self):
		import sys
		if self.f != sys.stdout:
			self.f.close()

