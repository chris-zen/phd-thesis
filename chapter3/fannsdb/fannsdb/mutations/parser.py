import re

from mutation import Mutation

Mutation.PROTEIN_RE = re.compile(r"^\*?([a-zA-Z0-9_])+$")
CHR_RE = re.compile(r"^(?:chr)?([XY]|1[0-9]|2[0-2]|[1-9])$", re.IGNORECASE)
INTEGER_RE = re.compile(r"^[0-9]+$")
NUCLEOTID_RE = re.compile(r"^[ACGT]$", re.IGNORECASE)
ALLELE_RE = re.compile(r"^([ACGT])[>/]([ACGT])$", re.IGNORECASE)
STRAND_RE = re.compile(r"^(\+|\+1|\-|\-1|1)$")
AMINOACID_RE = re.compile(r"^[ARNDCEQGHILKMFPSTWYV]$", re.IGNORECASE)
CHANGE_RE = re.compile(r"^([ARNDCEQGHILKMFPSTWYV])([0-9]+)([ARNDCEQGHILKMFPSTWYV])$", re.IGNORECASE)
IDENTIFIER_RE = re.compile(r"^[a-zA-Z0-9_]+$")

def init(sm):
	pass

def chromosome(sm):
	sm.mut.coord = Mutation.GENOMIC
	sm.mut.chr = sm.mut.protein = sm.token_groups[0]

def start(sm):
	sm.mut.start = int(sm.token)

def end(sm):
	sm.mut.end = int(sm.token)

def allele(sm):
	sm.mut.ref, sm.mut.alt = sm.token_groups

def ref(sm):
	sm.mut.alt = sm.token

def alt(sm):
	sm.mut.ref = sm.mut.alt
	sm.mut.alt = sm.token

def strand(sm):
	sm.mut.strand = sm.token

def protein(sm):
	sm.mut.protein = sm.token

def change(sm):
	sm.mut.coord = Mutation.PROTEIN
	sm.mut.chr = None
	sm.mut.ref, sm.mut.start, sm.mut.alt = sm.token_groups
	sm.mut.start = int(sm.mut.start)

def apos(sm):
	sm.mut.start = int(sm.token)

def aref(sm):
	sm.mut.coord = Mutation.PROTEIN
	sm.mut.chr = None
	sm.mut.alt = sm.token

def aalt(sm):
	sm.mut.coord = Mutation.PROTEIN
	sm.mut.chr = None
	sm.mut.ref = sm.mut.alt
	sm.mut.alt = sm.token

def identifier(sm):
	sm.mut.identifier = sm.token


class PrematureEnd(Exception):
	pass

class UnexpectedToken(Exception):
	pass

class ParserStateMachine(object):

	initial_state = None
	end_states = []
	transitions = {}
	handlers = {}

	def __init__(self):
		self.__reset()
		
	def __reset(self, line=None):
		self.line = line
		self._index = 0
		self.token = None
		self.token_groups = None
		self.remaining_fields = []
		self._state = self.initial_state
		self._init()

	def _init(self):
		raise NotImplemented()

	def _start_parse(self):
		pass

	def _end_parse(self):
		pass

	@property
	def parsed_data(self):
		return None

	def _next_token(self):
		if self._index > len(self.line):
			return None

		try:
			pos = self.line.index("\t", self._index)
		except ValueError:
			pos = len(self.line)

		token = self.line[self._index:pos]
		self._index = pos + 1
		return token

	def parse(self, line):
		self.__reset(line)

		self._start_parse()

		done = False
		while not done:
			# action
			self.handlers[self._state](self)

			# transition
			next_state = None
			self.token = self._next_token()
			if self.token is not None:
				for condition, state in self.transitions[self._state]:
					match = condition.match(self.token)
					if match:
						self.token_groups = match.groups()
						next_state = state
						break

			#print "{} ---[{}]--> {} | {}".format(self._state, self.token, next_state, repr(self))

			if next_state is None:
				done = True
				if self._state not in self.end_states:
					if self._index > len(self.line):
						raise PrematureEnd()
					else:
						raise UnexpectedToken(self.token)
			else:
				self._state = next_state

		token = self._next_token()
		while token is not None:
			self.remaining_fields += [token]
			token = self._next_token()

		self._end_parse()

		return self.parsed_data


class MutationParser(ParserStateMachine):

	def _init(self):
		self.mut = Mutation()

	def _start_parse(self):
		self.mut = Mutation()

	def _end_parse(self):
		self.mut.remaining_fields = self.remaining_fields

	@property
	def parsed_data(self):
		return self.mut

	def __repr__(self):
		m = self.mut
		sb = []
		if m.coord is None:
			sb += ["?"]
		else:
			sb += [m.coord, "chr:{}".format(m.chr) if m.coord == Mutation.GENOMIC else "protein:{}".format(m.protein)]
		if m.start is not None:
			sb += ["start:{}".format(m.start)]
		if m.end is not None:
			sb += ["end:{}".format(m.end)]
		if m.ref is not None:
			sb += ["ref:{}".format(m.ref)]
		if m.alt is not None:
			sb += ["alt:{}".format(m.alt)]
		if m.strand is not None:
			sb += ["strand:{}".format(m.strand)]
		if m.identifier is not None:
			sb += ["id:{}".format(m.identifier)]
		if len(m.remaining_fields) > 0:
			sb += ["extra:{}".format(";".join(m.remaining_fields))]
		return " ".join(sb)

class DnaAndProtMutationParser(MutationParser):

	initial_state = "INIT"

	end_states = ["ALLELE", "REF", "REF_NP", "ALT", "STRAND", "IDENTIFIER", "CHANGE", "AREF", "AALT"]

	transitions = {
		"INIT" : [
			(CHR_RE, "CHR"),
			(Mutation.PROTEIN_RE, "Mutation.PROTEIN")
		],
		"CHR" : [
			(INTEGER_RE, "START")
		],
		"START" : [
			(INTEGER_RE, "END"),
			(ALLELE_RE, "ALLELE"),
			(NUCLEOTID_RE, "REF")
		],
		"END" : [
			(ALLELE_RE, "ALLELE"),
			(NUCLEOTID_RE, "REF")
		],
		"ALLELE" : [
			(STRAND_RE, "STRAND"),
			(IDENTIFIER_RE, "IDENTIFIER")
		],
		"REF" : [
			(STRAND_RE, "STRAND"),
			(NUCLEOTID_RE, "ALT"),
			(AMINOACID_RE, "AALT"),
			(IDENTIFIER_RE, "IDENTIFIER")
		],
		"REF_NP" : [
			(STRAND_RE, "STRAND"),
			(NUCLEOTID_RE, "ALT"),
			(IDENTIFIER_RE, "IDENTIFIER")
		],
		"ALT" : [
			(STRAND_RE, "STRAND"),
			(IDENTIFIER_RE, "IDENTIFIER")
		],
		"STRAND" : [
			(IDENTIFIER_RE, "IDENTIFIER")
		],
		"Mutation.PROTEIN" : [
			(CHANGE_RE, "CHANGE"),
			(INTEGER_RE, "APOS")
		],
		"CHANGE" : [
			(IDENTIFIER_RE, "IDENTIFIER")
		],
		"APOS" : [
			(AMINOACID_RE, "AREF")
		],
		"AREF" : [
			(AMINOACID_RE, "AALT")
		],
		"AALT" : [
			(IDENTIFIER_RE, "IDENTIFIER")
		],
		"IDENTIFIER" : []
	}

	handlers = {
		"INIT" : init,
		"CHR" : chromosome,
		"START" : start,
		"END" : end,
		"ALLELE" : allele,
		"REF" : ref,
		"REF_NP" : ref,
		"ALT" : alt,
		"STRAND" : strand,
		"Mutation.PROTEIN" : protein,
		"CHANGE" : change,
		"APOS" : apos,
		"AREF" : aref,
		"AALT" : aalt,
		"IDENTIFIER" : identifier,
	}

class DnaMutationParser(MutationParser):

	initial_state = "INIT"

	end_states = ["ALLELE", "REF", "ALT", "STRAND", "IDENTIFIER"]

	transitions = {
		"INIT" : [
			(CHR_RE, "CHR")
		],
		"CHR" : [
			(INTEGER_RE, "START")
		],
		"START" : [
			(INTEGER_RE, "END"),
			(ALLELE_RE, "ALLELE"),
			(NUCLEOTID_RE, "REF")
		],
		"END" : [
			(ALLELE_RE, "ALLELE"),
			(NUCLEOTID_RE, "REF")
		],
		"ALLELE" : [
			(STRAND_RE, "STRAND"),
			(IDENTIFIER_RE, "IDENTIFIER")
		],
		"REF" : [
			(STRAND_RE, "STRAND"),
			(NUCLEOTID_RE, "ALT"),
			(IDENTIFIER_RE, "IDENTIFIER")
		],
		"ALT" : [
			(STRAND_RE, "STRAND"),
			(IDENTIFIER_RE, "IDENTIFIER")
		],
		"STRAND" : [
			(IDENTIFIER_RE, "IDENTIFIER")
		],
		"IDENTIFIER" : []
	}

	handlers = {
		"INIT" : init,
		"CHR" : chromosome,
		"START" : start,
		"END" : end,
		"ALLELE" : allele,
		"REF" : ref,
		"ALT" : alt,
		"STRAND" : strand,
		"IDENTIFIER" : identifier
	}
