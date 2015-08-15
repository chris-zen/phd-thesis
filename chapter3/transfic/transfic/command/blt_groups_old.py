#!/usr/bin/env python

import os
import argparse
import logging
import math

from collections import defaultdict

from bgcore import tsv
from bgcore import logging as bglogging

from fannsdb.cmdhelper import DefaultCommandHelper

DEFAULT_COUNT_THRESHOLD = 20
DEFAULT_STDEV_THRESHOLD = 1.0

def line_error(log, path, line, msg, code=-1):
	log.error("{}:{} {}".format(path, line, msg))
	exit(code)

def calculate_group(log, group, threshold,
					group_children, group_genes,
					partial_stats, num_predictors,
					stats, group_path=None):

	group_path = group_path or []

	# process first the children so the more specific terms have priority
	genes = group_genes.get(group, set())
	children = group_children.get(group, set())
	for child in children:
		genes.update(calculate_group(log, child, threshold,
									 group_children, group_genes,
									 partial_stats, num_predictors,
									 stats, group_path + [group]))

	genes_with_stats = set([g for g in genes if g in partial_stats])

	info = ["num_features={}, with_stats={}".format(len(genes), len(genes_with_stats))]

	# calculate group stats only if a minimum number of genes
	if len(genes_with_stats) >= threshold:
		# check which genes are still missing statistics
		genes_without_stats = set()
		for gene in genes:
			if gene not in stats:
				genes_without_stats.add(gene)

		# calculate group stats only if there are genes needing them
		if len(genes_without_stats) > 0:

			# accumulate partial statistics for the genes in this group
			group_partial_stats = [None] * num_predictors
			for i in range(num_predictors):
				group_partial_stats[i] = [0, 0.0, 0.0]

			for gene in genes_with_stats:
				gene_partial_stats = partial_stats[gene]
				for i in range(num_predictors):
					group_partial_stats[i][0] += gene_partial_stats[i][0]
					group_partial_stats[i][1] += gene_partial_stats[i][1]
					group_partial_stats[i][2] += gene_partial_stats[i][2]
					#if i==0: print "[[", i, "]] +++", gene_partial_stats[i], "(", gene, ") ==> ", group_partial_stats[i]

			# calculate group statistics
			group_stats = [None] * (num_predictors + 1)
			for i in range(num_predictors):
				s0, s1, s2 = group_partial_stats[i]

				if s0 == 0.0:
					continue

				x = (s0 * s2 - s1 * s1) / (s0 * (s0 - 1))
				if x < -1e12:
					continue

				mean = s1 / s0
				std = math.sqrt(abs(x))
				group_stats[i] = (int(s0), mean, std)

			# update gene statistics from group statistics if necessary
			for gene in genes:
				pos_code = []
				if gene not in stats:
					pos_code += ["+"] * num_predictors
					gene_stats = group_stats
				else:
					gene_stats = stats[gene]
					for i in range(num_predictors):
						if gene_stats[i] is None:
							pos_code += ["+"]
							gene_stats[i] = group_stats[i]
						else:
							pos_code += ["-"]

				if gene_stats[num_predictors] is None:
					gene_stats[num_predictors] = "{}|{}".format(group, "".join(pos_code))

				stats[gene] = gene_stats

			info += ["features_without_stats={}".format(len(genes_without_stats)), "group_stats={}".format(group_stats)]

	path = "{} ".format(">".join(group_path)) if len(group_path) > 0 else ""
	log.debug("{}[{}] {}".format(path, group, ", ".join(info)))

	return genes

def main():
	parser = argparse.ArgumentParser(
		description="Calculate Baseline Tolerance statistics per gene")

	cmd = DefaultCommandHelper(parser)

	parser.add_argument("tree_path", metavar="TREE_PATH",
						help="The groups descendant tree")

	parser.add_argument("root_group", metavar="ROOT_GROUP",
						help="Tree root group")

	parser.add_argument("group_genes_path", metavar="GROUP_FEATS_PATH",
						help="Map between groups and features")

	parser.add_argument("stats_path", metavar="STATS_PATH",
						help="Partial gene statistics")

	parser.add_argument("out_path", metavar="OUTPUT_PATH",
						help="Output gene statistics")

	parser.add_argument("-c", "--count-threshold", dest="count_threshold", metavar="N", default=DEFAULT_COUNT_THRESHOLD,
						help="Minimum number of features per group")

	parser.add_argument("--stdev-threshold", dest="stdev_threshold", metavar="V", default=DEFAULT_STDEV_THRESHOLD,
						help="Skip feature statistics with a standard deviation less than V (it will be calculated at the level of groups)")

	args, logger = cmd.parse_args("blt-groups")

	logger.info("Loading groups tree ...")

	group_children = defaultdict(set)
	with tsv.open(args.tree_path) as f:
		for group, children in tsv.lines(f, (str, lambda v: set(v.split(",")))):
			group_children[group] |= children

	logger.info("Loading mappings between groups and features ...")

	group_genes = defaultdict(set)
	with tsv.open(args.group_genes_path) as f:
		for group, genes in tsv.lines(f, (str, lambda v: set(v.split(",")))):
			group_genes[group] |= genes

	logger.info("Loading partial statistics ...")

	partial_stats = {}
	with tsv.open(args.stats_path) as f:
		predictors = f.readline().rstrip("\n").split("\t")[1:]
		num_predictors = len(predictors)
		for line in f:
			fields = line.rstrip("\n").split("\t")
			gene = fields[0]
			gene_stats = [[float(v) if i > 0 else int(v) for i, v in enumerate(ss.split("/"))] for ss in fields[1:]]
			partial_stats[gene] = gene_stats

	logger.info("  Predictors: {}".format(", ".join(predictors)))
	logger.info("  Features: {}".format(len(partial_stats.keys())))

	logger.info("Calculating features ...")

	stats = {}

	feat_count = 0
	feat_partial_count = [0] * num_predictors
	for feature, feat_partial_stats in partial_stats.items():
		feat_with_stats = False
		feat_stats = [None] * (num_predictors + 1)
		for i in range(num_predictors):
			s0, s1, s2 = feat_partial_stats[i]

			if s0 == 0.0:
				continue

			if s0 < args.count_threshold:
				continue

			x = (s0 * s2 - s1 * s1) / (s0 * (s0 - 1))
			if x < -1e-12:
				continue

			mean = s1 / s0
			std = math.sqrt(abs(x))
			if std < args.stdev_threshold:
				continue

			feat_stats[i] = (int(s0), mean, std)
			feat_partial_count[i] += 1
			feat_with_stats = True

		if feat_with_stats:
			feat_count += 1
			stats[feature] = feat_stats
			#print feature, "\t".join(["/".join([str(v) for v in feat_stats[i] or []]) for i in range(num_predictors)])


	logger.info("  {} ({}) features out of {} calculated directly from partial statistics".format(
		feat_count, "/".join(map(str, feat_partial_count)), len(partial_stats)))

	logger.info("Calculating groups ...")

	calculate_group(logger, args.root_group, args.count_threshold,
					group_children, group_genes,
					partial_stats, num_predictors,
					stats)

	logger.info("  {} features calculated in total".format(len(stats)))

	with tsv.open(args.out_path, "w") as of:
		tsv.write_line(of, "GENE", "GROUP", *predictors)
		for gene in sorted(stats.keys()):
			gene_stats = stats[gene]
			sb = [gene]
			stats_group = gene_stats[num_predictors]
			if stats_group is not None:
				sb += [stats_group]
			else:
				sb += ["|" + ("-" * num_predictors)]

			for i in range(num_predictors):
				if gene_stats[i] is not None:
					sb += ["/".join([str(v) for v in gene_stats[i]])]
				else:
					sb += ["-/-/-"]
			tsv.write_line(of, *sb)

	return 0

if __name__ == "__main__":
	exit(main())