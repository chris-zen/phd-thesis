class Mutation(object):
	GENOMIC = "G"
	PROTEIN = "P"

	def __init__(self):
		self.reset()

	def reset(self):
		self.coord = None
		self.protein = None
		self.chr = None
		self.start = None
		self.end = None
		self.ref = None
		self.alt = None
		self.strand = None
		self.identifier = None
		self.remaining_fields = []

	def __repr__(self):
		sb = []
		if self.coord is None:
			sb += ["?"]
		else:
			sb += [self.coord, "chr:{}".format(self.chr) if self.coord == Mutation.GENOMIC else "protein:{}".format(self.protein)]
		if self.start is not None:
			sb += ["start:{}".format(self.start)]
		if self.end is not None:
			sb += ["end:{}".format(self.end)]
		if self.ref is not None:
			sb += ["ref:{}".format(self.ref)]
		if self.alt is not None:
			sb += ["alt:{}".format(self.alt)]
		if self.strand is not None:
			sb += ["strand:{}".format(self.strand)]
		if self.identifier is not None:
			sb += ["id:{}".format(self.identifier)]
		if len(self.remaining_fields) > 0:
			sb += ["extra:{}".format(";".join(self.remaining_fields))]
		return " ".join(sb)