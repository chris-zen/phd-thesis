from bgcore import tsv

from parser import DnaAndProtMutationParser, PrematureEnd, UnexpectedToken

class MutationsParserReader(object):
	def __init__(self, path, skip_exc=False, header=False, parser=None):
		self.path = path
		self.skip_errors = skip_exc
		self.header = True
		self.__f = None
		self.line_num = 0
		self.__parser = parser or DnaAndProtMutationParser()

	def __open(self):
		self.__f = tsv.open(self.path)
		self.line_num = 0
		if self.header:
			tsv.skip_comments_and_empty(self.__f)

	def __close(self):
		if self.__f is not None:
			self.__f.close()
			self.__f = None

	def __readline(self):
		line = self.__f.readline()
		stripped_line = line.rstrip(" \n\r")
		self.line_num += 1
		while line.startswith("#") or (len(line) > 0 and len(stripped_line) == 0):
			line = self.__f.readline()
			stripped_line = line.rstrip(" \n\r")
			self.line_num += 1

		return line, stripped_line

	def __iter__(self):
		return self

	def next(self):
		if self.__f is None:
			self.__open()

		done = False
		while not done:
			line, stripped_line = self.__readline()

			if len(line) == 0:
				raise StopIteration

			line = stripped_line

			try:
				self.__parser.parse(line)
				done = True
			except PrematureEnd:
				if not self.skip_errors:
					raise
			except UnexpectedToken as ex:
				if not self.skip_errors:
					raise

		return self.__parser.mut