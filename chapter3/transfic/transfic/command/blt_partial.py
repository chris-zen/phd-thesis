#!/usr/bin/env python

import os
import argparse

from bgcore import tsv
from bgcore import logging as bglogging

from transfic.cmdhelper import DefaultCommandHelper

def line_error(log, path, line, msg, code=-1):
	log.error("{}:{} {}".format(path, line, msg))
	exit(code)

def main():
	parser = argparse.ArgumentParser(
		description="Calculate Baseline Tolerance partial statistics per feature")

	cmd = DefaultCommandHelper(parser)

	parser.add_argument("scores_path", metavar="SCORES_PATH",
						help="The scores file")

	parser.add_argument("predictors", metavar="PREDICTORS",
						help="Comma separated list of predictors")

	parser.add_argument("out_path", metavar="OUTPUT_PATH",
						help="Output file.")

	cmd.add_transform_args()

	args, logger = cmd.parse_args("blt-partial")

	predictors = [p.strip() for p in args.predictors.split(",") if len(p.strip()) > 0]
	num_predictors = len(predictors)

	if len(predictors) == 0:
		logger.error("At least one predictor is needed")
		exit(-1)

	logger.info("Selected predictors: {}".format(", ".join(predictors)))

	transforms = cmd.get_transforms()

	stats = {}

	lost_snvs = 0
	scores_path = args.scores_path

	logger.info("Reading scores from {} ...".format(
		os.path.basename(scores_path) if scores_path != "-" else "standard input"))

	with tsv.open(scores_path) as sf:
		for line_num, line in enumerate(sf):
			fields = line.rstrip("\n").split("\t")
			chrom, pos, ref, alt, feature = fields[:5]

			if len(feature) == 0:
				lost_snvs += 1
				continue

			scores = fields[5:]

			if len(scores) != num_predictors:
				line_error(logger, scores_path, line_num, "Number of score columns does not match the number of predictors")

			try:
				scores = [float(v) if len(v) > 0 else None for v in scores]
			except:
				line_error(logger, scores_path, line_num, "Scores should be real numbers: {}".format(scores))

			if feature not in stats:
				stats[feature] = tuple([[0, 0.0, 0.0] for p in predictors])

			feature_stats = stats[feature]

			for i, score in enumerate(scores):
				if score is not None:
					predictor = predictors[i]
					if predictor in transforms:
						for name, func in transforms[predictor]:
							try:
								score = func(score)
							except:
								logger.error("Error transforming the {} score {} with {}".format(predictor, score, name))
								exit(-1)

					feature_stats[i][0] += 1
					feature_stats[i][1] += score
					feature_stats[i][2] += score * score

	logger.info("Saving results into {} ...".format(
		os.path.basename(args.out_path) if args.out_path != "-" else "standard output"))

	with tsv.open(args.out_path, "w") as of:
		tsv.write_line(of, "FEATURE", *predictors)
		for feature in sorted(stats.keys()):
			sb = [feature]
			feature_stats = stats[feature]
			for i in range(num_predictors):
				sb += ["/".join([repr(v) for v in feature_stats[i]])]
			tsv.write_line(of, *sb)

	logger.info("Number of SNV's = {}, lost SNV's = {}, number of features = {}".format(line_num, lost_snvs, len(stats)))

	return 0

if __name__ == "__main__":
	exit(main())