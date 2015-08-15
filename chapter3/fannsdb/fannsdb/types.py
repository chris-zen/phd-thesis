def score_value(v):
	try:
		return float(v)
	except:
		if len(v) == 0:
			return None

		raise Exception("Wrong score value '{}'".format(v))

def position(v):
	try:
		pos = int(v)
		assert pos >= 0
		return pos
	except:
		raise Exception("Wrong position '{}'".format(v))

def nucleotide(v):
	if len(v) != 1:
		raise Exception("Only single nucleotides are allowed but found '{}'".format(v))
	return v.upper()

def aa(v):
	if len(v) != 1:
		raise Exception("Only single aminoacides are allowed but found '{}'".format(v))
	return v.upper()
