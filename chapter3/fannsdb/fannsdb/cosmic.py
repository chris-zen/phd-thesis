import os
import argparse
import tarfile
import re
import json
import logging
from collections import defaultdict

from bgcore import tsv
from bgcore.re import ReContext

from fannsdb.utils import RatedProgress

__CB = {
	"A" : "T",
	"T" : "A",
	"G" : "C",
	"C" : "G"
}

def complementary_sequence(seq):
	return "".join([__CB[base] if base in __CB else base for base in seq.upper()])

MUT_CDS_RE = re.compile(r"^c.\d+([ACGT]+)>([ACGT]+)$")
MUT_AA_RE = re.compile(r"^p.([ARNDCEQGHILKMFPSTWYV]+)(\d+)([ARNDCEQGHILKMFPSTWYV]+)$")
MUT_POS_RE = re.compile(r"(.+):(\d+)(-\d+)?")

class Dataset(object):
	def __init__(self, name):
		self.name = name
		self.f = None
		self._size = 0

	def __enter__(self):
		self.f = tsv.open(self.name, "w")
		self._size = 0
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.f is not None:
			self.f.close()

	def write(self, line):
		self._size += 1
		#self.f.write("{}\tID{}\n".format(line, self._size))
		self.f.write(line + "\n")

	@property
	def size(self):
		return self._size

def get_transcripts(fanns_db, mut_cds, mut_aa, mut_pos, mut_strand, acc, logger):
	fields = [mut_cds, mut_aa, mut_pos, mut_strand, acc]

	cds_ctx = ReContext(mut_cds)
	aa_ctx = ReContext(mut_aa)

	if cds_ctx.match(MUT_CDS_RE):
		ref, alt = [cds_ctx.group(i) for i in xrange(1, 3)]
		aa_ref_len = len(ref)
		if aa_ref_len != len(alt):
			logger.warn("Found substitution with different alleles: {}".format(fields))

		if mut_strand == "-":
			ref = complementary_sequence(ref)
			alt = complementary_sequence(alt)

		pos_ctx = ReContext(mut_pos)
		if not pos_ctx.match(MUT_POS_RE):
			logger.warn("Unexpected mutation position: {}".format(fields))
			return

		chrom, start = [pos_ctx.group(i) for i in xrange(1, 3)]
		if chrom == "25":
			return

		start = int(start)
		for i in xrange(aa_ref_len):
			#logger.info("{}{}:{}:{}/{}:{} ({}, {})".format(chrom, mut_strand, start+i, ref[i], alt[i], acc, mut_cds, mut_aa))
			for row in fanns_db.query_scores(chr=chrom, start=start + i, ref=ref[i], alt=alt[i],
												  strand=mut_strand, transcript=acc, maps=["symbol"]):
				#logger.info("  -> {}".format(row))
				yield row

	elif aa_ctx.match(MUT_AA_RE):
		aa_ref, aa_pos, aa_alt = [aa_ctx.group(i) for i in xrange(1, 4)]
		aa_ref_len = len(aa_ref)
		if aa_ref_len != len(aa_alt):
			logger.warn("Found substitution with different alleles: {}".format(fields))

		aa_pos = int(aa_pos)
		for i in xrange(aa_ref_len):
			for row in fanns_db.query_scores(protein=acc, aa_pos=aa_pos + i, aa_ref=aa_ref[i], aa_alt=aa_alt[i],
												  maps=["symbol", "prot_transcript"]):
				yield row

def extract_snvs(fanns_db, data_path, logger=None):

	logger = logger or logging.getLogger("perf-cosmic")

	snvs = dict()

	logger.info("Reading mutations ...")
	
	progress = RatedProgress(logger, name="mutations")
	
	with tsv.open(data_path, "r") as df:
		columns = [
			"Genome-wide screen",
			"Mutation Description",
			"Mutation CDS",
			"Mutation AA",
			"Mutation GRCh37 genome position",
			"Mutation GRCh37 strand",
			"Accession Number",
			"ID_sample"]

		total_rows = queried_rows = dbfound_rows = 0
		for fields in tsv.rows(df, columns=columns, header=True):
			total_rows += 1
			wide_screen, mut_desc, mut_cds, mut_aa, mut_pos, mut_strand, acc, sample_id = fields

			# wide_screen != "y"
			if mut_desc != "Substitution - Missense":
				continue

			queried_rows += 1
			for row in get_transcripts(fanns_db, mut_cds, mut_aa, mut_pos, mut_strand, acc, logger):
				dbfound_rows += 1
				k = tuple([row[k] for k in ["protein", "aa_pos", "aa_ref", "aa_alt"]])
				if k not in snvs:
					snvs[k] = snv = dict(
						transcript=row["transcript"],
						symbol=row["xrefs"]["symbol"],
						msamples=set(), wsamples=set())
				else:
					snv = snvs[k]
				
				if wide_screen == "y":
					snv["wsamples"].add(sample_id)
				else:
					snv["msamples"].add(sample_id)
			
			progress.update()

		progress.log_totals()

	logger.info("Counting the number of samples per mutation ...")
	
	for data in snvs.itervalues():
		data["msamples"] = len(data["msamples"])
		data["wsamples"] = len(data["wsamples"])
    
	logger.info("Total: total_rows={}, queried_rows={}, found_rows={}, protein_changes={}".format(total_rows, queried_rows, dbfound_rows, len(snvs)))

	return snvs


def save_snvs(snvs, path, header=False):
    with open(path, "w") as f:
    	if header:
	    	f.write("\t".join(["PROTEIN", "POS", "REF", "ALT", "SYM", "TRS", "MSAMPLES", "WSAMPLES"]) + "\n")
        for snv, data in snvs.iteritems():
            f.write("\t".join([str(v) for v in snv]) + "\t")
            symbols = data.get("symbol") or ""
            if isinstance(symbols, basestring):
                symbols = [symbols]
            f.write(",".join(symbols) + "\t" + (data.get("transcript") or "") + "\t")
            f.write("{}\t{}\n".format(data["msamples"], data["wsamples"]))


def load_snvs(path):
    snvs = {}
    with open(path) as f:
        for line in f:
            fields = line.rstrip("\n").split("\t")
            protein, pos, ref, alt = fields[0:4]
            symbols = fields[4].split(",")
            symbols = symbols[0] if len(symbols) == 1 else set(symbols)
            snvs[(protein, int(pos), ref, alt)] = dict(
                symbol=symbols,
                transcript=fields[5],
                msamples=int(fields[6]),
                wsamples=int(fields[7]))
    return snvs
   
   
def create_datasets(snvs, cgc_path, tdrivers_path, pdrivers_path, output_prefix, logger=None):

	logger = logger or logging.getLogger("perf-cosmic")

	prefix = output_prefix or "cosmic-"

	logger.info("Loading CGC genes ...")
	cgc_genes = set()
	with open(cgc_path, "r") as f:
		for line in f:
			cgc_genes.add(line.rstrip("\n"))

	logger.info("Loading TD drivers ...")
	tdrivers = set()
	with open(tdrivers_path, "r") as f:
		for line in f:
			tdrivers.add(line.rstrip("\n").split("\t")[0])

	logger.info("Loading PD drivers ...")
	pdrivers = set()
	with open(pdrivers_path, "r") as f:
		for line in f:
			pdrivers.add(line.rstrip("\n").split("\t")[0])

	logger.info("Creating datasets ...")

	progress = RatedProgress(logger, name="mutations")

	with Dataset(prefix + "1") as rec1,\
		Dataset(prefix + "2") as rec2,\
		Dataset(prefix + "4") as rec4,\
		Dataset(prefix + "CGC") as cgc,\
		Dataset(prefix + "noCGC") as nocgc,\
		Dataset(prefix + "TD") as td,\
		Dataset(prefix + "noTD") as notd,\
		Dataset(prefix + "PD") as pd,\
		Dataset(prefix + "noPD") as nopd:

		for (protein, aa_pos, aa_ref, aa_alt), snv in snvs.items():
			num_samples = len(snv["samples"])
			line = "\t".join([str(v) for v in [protein, aa_pos, aa_ref, aa_alt]])
			symbol = snv["symbol"] or ""
			if isinstance(symbol, basestring):
				symbol = set([symbol])
			elif isinstance(symbol, list):
				symbol = set(symbol)

			if num_samples == 1:
				rec1.write(line)

			if num_samples >= 2:
				rec2.write(line)

			if num_samples >= 4:
				rec4.write(line)

			if len(symbol & cgc_genes) > 0:
				cgc.write(line)
			elif num_samples == 1:
				nocgc.write(line)

			if len(symbol & tdrivers) > 0:
				td.write(line)
			elif num_samples == 1:
				notd.write(line)

			if len(symbol & pdrivers) > 0:
				pd.write(line)
			elif num_samples == 1:
				nopd.write(line)

			progress.update()

		progress.log_totals()

		logger.info("Datasets: {}".format(", ".join(["{}={}".format(os.path.basename(d.name), d.size) for d in [
			rec1, rec2, rec4, cgc, nocgc, td, notd, pd, nopd]])))

