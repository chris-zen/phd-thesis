#!/usr/bin/env python

import os
import argparse
import logging
from datetime import datetime

from bgcore import tsv
from bgcore import logging as bglogging

def main():
	parser = argparse.ArgumentParser(
		description="Prepare SNV's dataset from individual training sets")

	parser.add_argument("pos_path", metavar="POS_SET",
						help="The positive training set file")

	parser.add_argument("neg_path", metavar="NEG_SET",
						help="The negative training set file")

	parser.add_argument("-m", "--map", dest="map_path", metavar="MAP",
						help="Optional mapping file for feature id's. Format: DST SRC")

	parser.add_argument("-o", dest="out_path", metavar="PATH",
						help="Output file. Use - for standard output.")

	bglogging.add_logging_arguments(parser)

	args = parser.parse_args()

	bglogging.initialize(args)

	logger = bglogging.get_logger("training-sets")

	if args.out_path is None:
		prefix = os.path.commonprefix([
							os.path.splitext(os.path.basename(args.pos_path))[0],
							os.path.splitext(os.path.basename(args.neg_path))[0]])

		prefix = prefix.rstrip(".")

		args.out_path = os.path.join(os.getcwd(), "{}-training.tsv".format(prefix))

	if args.map_path is not None:
		logger.info("Loading map ...")

		prot_map = {}
		with tsv.open(args.map_path) as f:
			for dst_feature, src_feature in tsv.lines(f, (str, str)):
					if len(src_feature) > 0:
						if src_feature not in prot_map:
							prot_map[src_feature] = set([dst_feature])
						else:
							prot_map[src_feature].add(dst_feature)
	else:
		prot_map = None
	
	logger.info("Processing ...")

	hits = dict(POS=0, NEG=0)
	fails = dict(POS=0, NEG=0)

	start_time = datetime.now()

	with tsv.open(args.out_path, "w") as wf:

		for event_type, path in (("POS", args.pos_path), ("NEG", args.neg_path)):

			logger.info("  [{}] Reading {} ...".format(event_type, path))

			with tsv.open(path) as f:
				types = (str, int, str, str)
				for protein, pos, aa1, aa2 in tsv.lines(f, types):
					protein = protein.strip()

					if prot_map is not None:
						if protein not in prot_map:
							logger.debug("[{}] Unmapped protein: {}".format(event_type, protein))
							fails[event_type] += 1
							continue
						proteins = prot_map[protein]
					else:
						proteins = [protein]

					hits[event_type] += 1

					for p in proteins:
						tsv.write_line(wf, p, pos, aa1.strip(), aa2.strip(), event_type)

	logger.info("               POS       NEG")
	logger.info("SNVs      {POS:>8}  {NEG:>8}".format(**hits))
	if args.map_path is not None:
		logger.info("unmapped  {POS:>8}  {NEG:>8}".format(**fails))

	logger.info("Finished. Elapsed time: {}".format(datetime.now() - start_time))

if __name__ == "__main__":
	main()
