"""
Sequence Ontology terms and functions related to VEP and IntOGenSM
"""

EMPTY = set()

SYNONYMOUS = set(["synonymous_variant"])

NON_SYNONYMOUS = set(["missense_variant"])

STOP = set(["stop_gained", "stop_lost"])

FRAMESHIFT = set(["frameshift_variant"])

SPLICE_JUNCTION = set(["splice_donor_variant", "splice_acceptor_variant"])

SPLICE_REGION = set(["splice_region_variant"])

CODON = set(["initiator_codon_variant", "incomplete_terminal_codon_variant"])

INFRAME = set(["inframe_deletion", "inframe_insertion"])

CODING_REGION = SYNONYMOUS | NON_SYNONYMOUS | STOP | FRAMESHIFT | SPLICE_JUNCTION | SPLICE_REGION | CODON | INFRAME

ONCODRIVEFM = SYNONYMOUS | NON_SYNONYMOUS | STOP | FRAMESHIFT

ONCODRIVECLUST = NON_SYNONYMOUS | STOP | CODON | SPLICE_JUNCTION

def match(terms, ruleset, optional_terms=EMPTY):
	if isinstance(terms, basestring):
		terms = [terms]

	if optional_terms is None:
		for term in terms:
			if term in ruleset:
				return True
	else:
		for term in terms:
			if term in ruleset or term in optional_terms:
				return True
	return False