#!/usr/bin/env python

import os
import argparse
import logging

from bgcore import tsv
from bgcore import logging as bglogging


def main():
	parser = argparse.ArgumentParser(
		description="Extract mutations in VCF and save as simple tabulated file")

	parser.add_argument("vcf_paths", metavar="PATH", nargs="+",
						help="The VCF files")

	parser.add_argument("-o", dest="out_path", metavar="PATH",
						help="Output file. Use - for standard output.")

	bglogging.add_logging_arguments(self._parser)

	args = parser.parse_args()

	bglogging.initialize(self.args)

	log = bglogging.get_logger("vcf-to-snvs")

	if args.out_path is None:
		names = []
		for path in args.vcf_paths:
			if path != "-":
				base_path, name, ext = tsv.split_path(path)
				names += [name]

		prefix = os.path.commonprefix(*names) if len(names) > 0 else ""
		prefix = prefix.rstrip(".")
		if len(prefix) == 0:
			prefix = "genome"
		args.out_path = "{}.tsv.gz".format(prefix)

	with tsv.open(args.out_path, "w") as outf:
		tsv.write_line(outf, "CHR", "POS", "REF", "ALT")

		for path in args.vcf_paths:
			log.info("Reading {} ...".format(path))

			with tsv.open(path) as inf:
				types = (str, str, str, str)
				columns = [0, 1, 3, 4]
				for fields in tsv.lines(inf, types, columns=columns):
					chrom, pos, ref, alt = fields

					#ref = ref.upper().strip("N")
					#alt = alt.upper().strip("N")

					ref_len = len(ref)
					alt_len = len(alt)

					if ref_len != alt_len or ref_len == 0 or alt_len == 0:
						continue

					try:
						pos = int(pos)
					except:
						continue

					if ref_len == 1:
						tsv.write_line(outf, chrom, pos, ref, alt)
					else:
						for i in range(ref_len):
							tsv.write_line(outf, chrom, pos + i, ref[i], alt[i])

if __name__ == "__main__":
	main()
