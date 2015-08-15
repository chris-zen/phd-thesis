#!/usr/bin/env python

import os
import argparse
import tarfile
import re

from collections import defaultdict

from bgcore import tsv
from bgcore.re import ReContext

from fannsdb.cmdhelper import DefaultCommandHelper
from fannsdb.utils import RatedProgress

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
		self.f.write("{}\tID{}\n".format(line, self._size))

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

		pos_ctx = ReContext(mut_pos)
		if not pos_ctx.match(MUT_POS_RE):
			logger.warn("Unexpected mutation position: {}".format(fields))
			return

		chrom, start = [pos_ctx.group(i) for i in xrange(1, 3)]
		if chrom == "25":
			return

		start = int(start)
		for i in xrange(aa_ref_len):
			for row in fanns_db.query_scores(chr=chrom, start=start + i, ref=ref[i], alt=alt[i],
												  transcript=acc, maps=["symbol"]): # strand=mut_strand, 
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

def main():
	parser = argparse.ArgumentParser(
		description="Generate datasets needed to evaluate performance from Cosmic mutations")

	cmd = DefaultCommandHelper(parser)

	cmd.add_db_args()

	parser.add_argument("data_path", metavar="PATH",
						help="The CosmicMutantExport tsv file")

	parser.add_argument("cgc_path", metavar="PATH",
						help="The list of CGC genes")

	parser.add_argument("drivers_path", metavar="PATH",
						help="The list of CHASM drivers (drivers.tmps)")

	parser.add_argument("-o", dest="prefix", metavar="PREFIX",
						help="Output prefix.")

	args, logger = cmd.parse_args("perf-cosmic")

	prefix = args.prefix or "cosmic-"

	fanns_db = cmd.open_db()

	try:
		snvs = dict()

		logger.info("Counting the number of samples per mutation ...")
		with tsv.open(args.data_path, "r") as df:
			columns = [
				#"Genome-wide screen",
				"Mutation Description",
				"Mutation CDS",
				"Mutation AA",
				"Mutation GRCh37 genome position",
				"Mutation GRCh37 strand",
				"Accession Number",
				"ID_sample"]

			total_rows = queried_rows = 0
			for fields in tsv.rows(df, columns=columns, header=True):
				total_rows += 1
				#wide_screen, mut_desc, mut_cds, mut_aa, mut_pos, mut_strand, acc, sample_id = fields
				mut_desc, mut_cds, mut_aa, mut_pos, mut_strand, acc, sample_id = fields
				wide_screen = "y"		
				if wide_screen != "y" or mut_desc != "Substitution - Missense":
					continue

				queried_rows += 1
				for row in get_transcripts(fanns_db, mut_cds, mut_aa, mut_pos, mut_strand, acc, logger):
					k = tuple([row[k] for k in ["protein", "aa_pos", "aa_ref", "aa_alt"]])
					if k not in snvs:
						symbol = row["xrefs"]["symbol"]
						snvs[k] = dict(
							transcript=row["transcript"],
							symbol=symbol,
							samples=set([sample_id]))
					else:
						snvs[k]["samples"].add(sample_id)

		logger.info("Total: total_rows={}, queried_rows={}, protein_changes={}".format(total_rows, queried_rows, len(snvs)))

		logger.info("Loading CGC genes ...")
		cgc_genes = set()
		with open(args.cgc_path, "r") as f:
			for line in f:
				cgc_genes.add(line.rstrip("\n"))

		logger.info("Loading CHASM drivers ...")
		drivers = set()
		with open(args.drivers_path, "r") as f:
			for line in f:
				drivers.add(line.rstrip("\n").split("\t")[0])

		logger.info("Creating datasets ...")

		progress = RatedProgress(logger, name="mutations")

		with Dataset(prefix + "1") as rec1,\
			Dataset(prefix + "2") as rec2,\
			Dataset(prefix + "4") as rec4,\
			Dataset(prefix + "CGC") as cgc,\
			Dataset(prefix + "noCGC") as nocgc,\
			Dataset(prefix + "D") as drv,\
			Dataset(prefix + "O") as nodrv:

			for (protein, aa_pos, aa_ref, aa_alt), snv in snvs.items():
				num_samples = len(snv["samples"])
				line = "\t".join([str(v) for v in [protein, aa_pos, aa_ref, aa_alt]])
				if num_samples == 1:
					rec1.write(line)
				if num_samples >= 2:
					rec2.write(line)
				if num_samples >= 4:
					rec4.write(line)
				
				symbol = snv["symbol"]
				if symbol is not None and ((isinstance(symbol, basestring) and symbol in cgc_genes) or len(set(symbol) & cgc_genes) > 0):
					cgc.write(line)
				elif num_samples == 1:
					nocgc.write(line)
			
				if snv["transcript"] in drivers:
					drv.write(line)
				elif num_samples == 1:
					nodrv.write(line)
                    
				progress.update()

			progress.log_totals()

			logger.info("Datasets: {}".format(", ".join(["{}={}".format(os.path.basename(d.name), d.size) for d in [
				rec1, rec2, rec4, cgc, nocgc, drv, nodrv]])))

	except:
		cmd.handle_error()

	return 0

if __name__ == "__main__":
	exit(main())
