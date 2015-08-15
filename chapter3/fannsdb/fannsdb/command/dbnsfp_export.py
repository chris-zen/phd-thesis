#!/bin/env python

import os
import re
import argparse
import time
import tempfile
import shutil
from zipfile import ZipFile
from datetime import timedelta

from bgcore import tsv
from fannsdb.cmdhelper import DefaultCommandHelper
from fannsdb.utils import hsize
from fannsdb.db.sqlitedb import CHR_INDEX, BASE_INDEX, AA_INDEX


def safe_float(v):
	try:
		return float(v)
	except:
		return None

def safe_int(v):
	try:
		return int(v)
	except:
		return None

def main():
	parser = argparse.ArgumentParser(
		description="Export dbNSFP scores")

	cmd = DefaultCommandHelper(parser)

	parser.add_argument("source_path", metavar="SOURCE",
						help="The original zip file")

	parser.add_argument("ensp_map_path", metavar="MAP",
						help="The mapping between Ensembl protein id's and Ensembl transcript id's and Uniprot id's")

	parser.add_argument("uniprot_map_path", metavar="MAP",
						help="The mapping between Ensembl protein id's and Uniprot id's")

	parser.add_argument("-o", "--output", dest="out_path", metavar="OUT_PATH",
						help="The output file")

	parser.add_argument("--temp", dest="temp_path", metavar="TEMP_PATH",
						help="A temporary path for zip extraction")

	parser.add_argument("--chr", dest="chr", metavar="CHROMOSOMES",
						help="Chromosomes to include: list separated by commas.")

	parser.add_argument("--skip-empty-scores", dest="skip_empty_scores", action="store_true", default=False,
						help="Skip SNV's where all the scores are empty")

	args, logger = cmd.parse_args("dbnsfp-export")

	if args.out_path is None:
		basename = os.path.basename(args.source_path)
		prefix = os.path.splitext(basename)[0]
		args.out_path = "{}.tsv.gz".format(prefix)

	logger.info("Loading maps ...")

	uniprot_map = {}
	trs_map = {}
	with tsv.open(args.ensp_map_path) as f:
		for ensp, enst in tsv.lines(f, (str, str)):
			if len(enst) > 0:
				trs_map[enst] = ensp

	with tsv.open(args.uniprot_map_path) as f:
		for ensp, uniprot_id in tsv.lines(f, (str, str)):
			if len(uniprot_id) > 0:
				uniprot_map[uniprot_id] = ensp

	logger.info("Opening {} ...".format(args.source_path))

	chromosomes = None
	if args.chr is not None:
		chromosomes = [c.strip().upper() for c in args.chr.split(",") if len(c.strip()) > 0]
		logger.info("Selected chromosomes: {}".format(", ".join(chromosomes)))
		chromosomes = set(chromosomes)

	name_pattern = re.compile(r"dbNSFP.+_variant.chr(.+)")

	COLUMNS = [
		"#chr", "pos(1-coor)", "ref", "alt", "cds_strand",
		"genename", "Uniprot_id", "Uniprot_aapos", "aaref", "aaalt",
		"Ensembl_geneid", "Ensembl_transcriptid", "aapos",
		"SIFT_score",
		"Polyphen2_HVAR_score",
		"MutationAssessor_score",
		"FATHMM_score",
		"MutationTaster_score",
#		"GERP_RS",
		"GERP++_RS",
#		"PhyloP_score"
		"phyloP"
	]

	tmp_prefix = args.temp_path or tempfile.gettempdir()
	if not os.path.exists(tmp_prefix):
		os.makedirs(tmp_prefix)
	if tmp_prefix[-1] != "/":
		tmp_prefix += "/"

	extract_path = tempfile.mkdtemp(prefix=tmp_prefix)

	try:
		logger.info("Output: {}".format(args.out_path if args.out_path != "-" else "standard output"))

		total_start_time = time.time()
		total_lines = 0
		with ZipFile(args.source_path, "r") as zf,\
			tsv.open(args.out_path, "w") as of: #,\
			#tsv.open(args.noprot_path, "w") as npf:

			tsv.write_line(of, "CHR", "STRAND", "START", "REF", "ALT", "TRANSCRIPT",
						   "PROTEIN", "AA_POS", "AA_REF", "AA_ALT",
						   "SIFT", "PPH2", "MA", "FATHMM", "MT", "GERPRS", "PHYLOP")

			#tsv.write_line(npf, "#CHR", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO")

			entries = []
			for entry in zf.infolist():
				m = name_pattern.match(entry.filename)
				if not m:
					continue

				chr = m.group(1)
				index = CHR_INDEX[chr] if chr in CHR_INDEX else 99

				if chromosomes is not None and chr not in chromosomes:
					logger.debug("Skipping chromosome {} ...".format(chr))
					continue

				entries += [(index, chr, entry)]

			for index, chr, entry in sorted(entries, key=lambda x: x[0]):
				logger.info("Reading chromosome {} ...".format(chr))

				zf.extract(entry, extract_path)
				fpath = os.path.join(extract_path, entry.filename)
				with open(fpath) as f:
					# Parse header
					hdr_line = f.readline()
					hdr = {}
					for index, name in enumerate(hdr_line.rstrip("\n").split("\t")):
						hdr[name] = index
					columns = [hdr[name] if name in hdr else None for name in COLUMNS]

					read = set()

					start_time = time.time()
					partial_start_time = start_time
					for line_num, line in enumerate(f, start=2):
						fields = line.rstrip("\n").split("\t")

						try:
							fields = [fields[i] if i is not None and i < len(fields) else None for i in columns]

							(chr, start, ref, alt, strand,
							 symbol, uniprot, uniprot_aapos, aa_ref, aa_alt,
							 gene, transcript, aapos,
							 sift, pph2, ma, fathmm,
							 mt, gerprs, phylop) = fields
							
							start = safe_int(start)
							ref = ref.upper() if ref is not None else None
							alt = alt.upper() if alt is not None else None
							aa_ref = aa_ref.upper() if aa_ref is not None else None
							aa_alt = aa_alt.upper() if aa_alt is not None else None
							sift = safe_float(sift)
							ma = safe_float(ma)
							fathmm = safe_float(fathmm)
							mt = safe_float(mt)
							gerprs = safe_float(gerprs)
							phylop = safe_float(phylop)

							if start is None or ref is None or alt is None:
								logger.warn("None value for pos or ref or alt at line {}: {}".format(line_num, fields))
								continue
							elif ref not in BASE_INDEX or alt not in BASE_INDEX:
								logger.warn("Unknown ref or alt at line {}: {}".format(line_num, fields))
								continue
							elif len(ref) != 1 or len(alt) != 1:
								logger.warn("Length != 1 for ref or alt len at line {}: {}".format(line_num, fields))
								continue
							#elif aa_ref not in AA_INDEX or aa_alt not in AA_INDEX:
							#	logger.warn("Unknown aa_ref or aa_alt at line {}: {}".format(line_num, fields))
							#	continue
							elif transcript is None or aapos is None or uniprot is None or uniprot_aapos is None:
								logger.warn("None value for transcript or aapos or uniprot or uniprot_aapos at line {}: {}".format(line_num, fields))
								continue

							if aa_ref not in AA_INDEX:
								aa_ref = None
							if aa_alt not in AA_INDEX:
								aa_alt = None

							trs_values = transcript.split(";")

							aapos_values = [safe_int(v) for v in aapos.split(";")]
							l = len(trs_values) - len(aapos_values)
							if l > 0:
								aapos_values += [aapos_values[-1]] * l

							uniprot_values = uniprot.split(";")
							uniprot_aapos_values = [safe_int(v) for v in uniprot_aapos.split(";")]
							l = len(uniprot_values) - len(uniprot_aapos_values)
							if l > 0:
								uniprot_aapos_values += [uniprot_aapos_values[-1]] * l

							pph2_values = [safe_float(v) for v in pph2.split(";")] if pph2 is not None else [None]
							l = len(uniprot_values) - len(pph2_values)
							if l > 0:
								pph2_values += [pph2_values[-1]] * l

							uniprot_index = {}
							for i, id in enumerate(uniprot_values):
								if uniprot_aapos_values[i] is not None:
									uniprot_index[uniprot_aapos_values[i]] = i

							for i, trs in enumerate(trs_values):
								pos = aapos_values[i]
								if pos < 0:
									pos = None

								if pos is not None and pos in uniprot_index:
									j = uniprot_index[pos]
									uniprot_value = uniprot_values[j]
									pph2_value = pph2_values[j]
								else:
									uniprot_value = pph2_value = None

								if trs in trs_map:
									prot_id = trs_map[trs]
								elif uniprot_value in uniprot_map:
									prot_id = uniprot_map[uniprot_value]
								else:
									logger.warn("Couldn't map neither protein {} or transcript {} at line {}: {}".format(uniprot_value, trs, line_num, "|".join([str(v) for v in fields])))
									continue

								#if pos < 0:
								#	logger.warn("Negative protein position at line {}: {}".format(line_num, pos))
								#	continue
								#elif ...
								if pph2_value is not None and (pph2_value < 0.0 or pph2_value > 1.0):
									logger.warn("PPH2 score {} out of range at line {}: {}".format(pph2_value, line_num, fields))
									continue

								if aa_alt == "X": # fix stop codons having a sift score
									sift = None

								if args.skip_empty_scores and sift is None and pph2_value is None and ma is None \
										and mt is None and gerprs is None and phylop is None:
									continue

								#log.info((chr, strand, start, ref, alt, aapos_values[i], aa_ref, aa_alt, trs, sift, pph2_value, ma))

								if pos is None or aa_ref is None or aa_alt is None:
									pass #tsv.write_line(npf, chr, start, ".", ref, alt, ".", "PASS",
										#		   "dbNSFP={}|{}|{}|{}|{}|{}".format(trs, prot_id,
										#					sift or "", pph2_value or "", ma or "", fathmm or ""))
								else:
									tsv.write_line(of, chr, strand, start, ref, alt, trs,
												   prot_id, pos, aa_ref, aa_alt,
												   sift, pph2_value, ma, fathmm,
												   mt, gerprs, phylop)

						except KeyboardInterrupt:
							raise
						except:
							logger.warn("Malformed line {}: {}".format(line_num, "|".join([str(v) for v in fields])))
							raise #continue

						partial_time = time.time() - partial_start_time
						if partial_time >= 5.0:
							partial_start_time = time.time()
							elapsed_time = time.time() - start_time
							logger.debug("  {} lines, {:.1f} lines/second".format(hsize(line_num-1), (line_num-1) / float(elapsed_time)))

					total_lines += line_num

					logger.info("  >  {} lines, {:.1f} lines/second".format(hsize(line_num), line_num / float(time.time() - start_time)))
					logger.info("  >> {} lines, {:.1f} lines/second".format(hsize(total_lines), total_lines / float(time.time() - total_start_time)))

				os.remove(fpath)

		total_elapsed_time = timedelta(seconds=time.time() - total_start_time)
		logger.info("Finished successfully. Elapsed time: {}".format(total_elapsed_time))

	except:
		return cmd.handle_error()
	finally:
		shutil.rmtree(extract_path)

	return 0

if __name__ == "__main__":
	exit(main())
