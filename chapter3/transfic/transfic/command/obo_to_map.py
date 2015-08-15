#!/usr/bin/env python

import os
import argparse
import logging

from bgcore import tsv
from bgcore import obo
from bgcore import logging as bglogging

def main():
	parser = argparse.ArgumentParser(
		description="Create a tree for the terms with the relation is_a in an OBO ontology")

	parser.add_argument("obo_path", metavar="PATH",
						help="The OBO file")

	parser.add_argument("-o", dest="out_path", metavar="PATH",
						help="Output file")

	parser.add_argument("--asc", dest="asc", action="store_true", default=False,
						help="Generate ascending tree (child -> parents)")

	parser.add_argument("--desc", dest="desc", action="store_true", default=False,
						help="Generate descending tree (parent -> children)")

	parser.add_argument("--compact", dest="compact", action="store_true", default=False,
						help="One line for each term with the related terms separated by commas")

	bglogging.add_logging_arguments(parser)

	args = parser.parse_args()

	log = bglogging.get_logger("vcf-to-snvs")

	if args.out_path is None:
		args.out_path = os.path.join(
			os.path.dirname(args.obo_path),
			"{}.map".format(os.path.splitext(os.path.basename(args.obo_path))[0]))

	if not args.asc and not args.desc:
		args.desc = True

	log.info("Parsing {} ...".format(args.obo_path))

	op = obo.parser.OboSimpleParser()
	ontology = op.parse(args.obo_path)

	log.info("Creating trees ...")

	asc_tree, desc_tree = obo.tree.all(ontology)

	if args.asc:
		if args.desc:
			name, ext = os.path.splitext(os.path.basename(args.out_path))
			if len(ext) > 0:
				name = "{}-asc{}".format(name, ext)
			else:
				name = "{}-asc".format(name)
			out_path = os.path.join(os.path.dirname(args.out_path), name)
		else:
			out_path = args.out_path

		log.info("Saving ascending tree into {} ...".format(out_path))

		with tsv.open(out_path, "w") as f:
			if args.compact:
				for key, values in sorted(asc_tree.items(), key=lambda v: v[0]):
					tsv.write_line(f, key, ",".join(sorted(values)))
			else:
				for key, values in sorted(asc_tree.items(), key=lambda v: v[0]):
					for value in sorted(values):
						tsv.write_line(f, key, value)

	if args.desc:
		if args.asc:
			name, ext = os.path.splitext(os.path.basename(args.out_path))
			if len(ext) > 0:
				name = "{}-desc{}".format(name, ext)
			else:
				name = "{}-desc".format(name)
			out_path = os.path.join(os.path.dirname(args.out_path), name)
		else:
			out_path = args.out_path

		log.info("Saving descending tree into {} ...".format(out_path))

		with tsv.open(out_path, "w") as f:
			if args.compact:
				for key, values in sorted(desc_tree.items(), key=lambda v: v[0]):
					tsv.write_line(f, key, ",".join(sorted(values)))
			else:
				for key, values in sorted(desc_tree.items(), key=lambda v: v[0]):
					for value in sorted(values):
						tsv.write_line(f, key, value)

if __name__ == "__main__":
	main()
