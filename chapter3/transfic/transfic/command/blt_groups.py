#!/usr/bin/env python

import os
import argparse
import logging
import math
import json

from collections import defaultdict
from datetime import datetime

from bgcore import tsv
from bgcore import logging as bglogging

from fannsdb.cmdhelper import DefaultCommandHelper

DEFAULT_COUNT_THRESHOLD = 20
DEFAULT_STDEV_THRESHOLD = 1.0

class BLT(object):
	LOCAL = "L"
	DEEP = "D"

	def __init__(self, n=0, mean=0, stdev=0, num_partials=0, from_node=None, scope=None):
		self.n = n
		self.mean = mean
		self.stdev = stdev
		self.num_partials = num_partials
		self.from_node = from_node
		self.scope = scope

class PartialBLT(object):
	def __init__(self, s0=0, s1=0, s2=0, sources=None):
		self.s0 = s0
		self.s1 = s1
		self.s2 = s2
		self.sources = sources or set()

	def copy(self, sources=None):
		return PartialBLT(
			s0=self.s0,
			s1=self.s1,
			s2=self.s2,
			sources=sources or self.sources.copy())

	def __iadd__(self, other):
		self.s0 += other.s0
		self.s1 += other.s1
		self.s2 += other.s2
		self.sources |= other.sources
		return self

	def calc_blt(self, count_threshold, stdev_threshold, from_node, scope):
		s0, s1, s2 = self.s0, self.s1, self.s2

		if s0 == 0.0 or s0 < count_threshold:
			return None

		x = (s0 * s2 - s1 * s1) / (s0 * (s0 - 1))
		if x < -1e-12:
			return None

		n = int(s0)
		mean = s1 / s0
		stdev = math.sqrt(abs(x))

		if stdev < stdev_threshold:
			return None

		return BLT(
			n, mean, stdev,
			num_partials=len(self.sources),
			from_node=from_node, scope=scope)

class Tree(object):
	def __init__(self, descendant_relations=None):
		self.nodes = {}

		for name, children in (descendant_relations or {}).items():
			self.add_node(name, children)

	def add_node(self, name, children_names=None):
		node = self.get_or_create_node(name)

		for child_name in children_names:
			child_node = self.get_or_create_node(child_name)
			node.children.add(child_node)

		return node

	def get_or_create_node(self, name):
		if name not in self.nodes:
			self.nodes[name] = node = Node(name)
		else:
			node = self.nodes[name]

		return node

	def get_node(self, name):
		return self.nodes.get(name)

	@property
	def node_count(self):
		return len(self.nodes)

class Node(object):
	def __init__(self, name, children=None):
		self.name = name
		self.children = children or set()
		self.local_sources = None
		self.deep_sources = None

		self.blt = defaultdict(lambda: None)
		self.pblt = defaultdict(lambda: None)
		self.pblt_sources = defaultdict(set)

	def __eq__(self, other):
		return isinstance(other, Node) and self.name == other.name

	def __hash__(self):
		return hash(self.name)

	def is_leaf(self):
		return len(self.children) == 0

	def has_pblt(self, predictor):
		return self.pblt[predictor] is not None

	def set_pblt(self, predictor, pblt):
		self.pblt[predictor] = pblt

	def get_pblt(self, predictor):
		return self.pblt.get(predictor)

	def has_blt(self, predictor):
		return self.blt[predictor] is not None

	def calc_blt(self, predictor, threshold):
		if self.has_pblt(predictor):
			self.blt[predictor] = self.pblt[predictor].calc_blt(self.name, threshold)
		else:
			self.blt[predictor] = BLT(source=self.name)

	def set_blt(self, predictor, blt):
		self.blt[predictor] = blt

	def get_blt(self, predictor):
		return self.blt.get(predictor)


def line_error(log, path, line, msg, code=-1):
	log.error("{}:{} {}".format(path, line, msg))
	exit(code)

def get_local_pblt_sources(node, predictor):

	if node.local_sources is not None:
		return node.local_sources

	sources = set()
	for child in node.children:
		if child.is_leaf and child.has_pblt(predictor):
			#return node.get_pblt(predictor).sources
			sources.add(child)

	node.local_sources = sources

	return sources

def get_deep_pblt_sources(node, predictor):

	if node.deep_sources is not None:
		return node.deep_sources

	if node.is_leaf and node.has_pblt(predictor):
		#return node.get_pblt(predictor).sources
		return set([node])

	sources = set()
	for child in node.children:
		sources.update(get_deep_pblt_sources(child, predictor))

	node.deep_sources = sources

	return sources

def calculate_pblt(sources, predictor):
	pblt = PartialBLT()
	for node in sources:
		source_pblt = node.get_pblt(predictor)
		if source_pblt is None:
			continue
		pblt += source_pblt
	return pblt

def calculate_blt(parent, node, predictor, count_threshold, stdev_threshold, logger):

	local_sources = get_local_pblt_sources(node, predictor)

	local_pblt = calculate_pblt(local_sources, predictor)

	if local_pblt.s0 < count_threshold:

		deep_sources = get_deep_pblt_sources(node, predictor)

		deep_pblt = calculate_pblt(deep_sources, predictor)

		if deep_pblt.s0 < count_threshold:
			blt = parent.get_blt(predictor) if parent is not None else None
		else:
			blt = deep_pblt.calc_blt(count_threshold, stdev_threshold, from_node=node.name, scope=BLT.DEEP)
	else:
		blt = local_pblt.calc_blt(count_threshold, stdev_threshold, from_node=node.name, scope=BLT.LOCAL)

	if blt is not None:
		prev_blt = node.get_blt(predictor)
		if prev_blt is None or (blt.n >= count_threshold and blt.num_partials < prev_blt.num_partials):
			node.set_blt(predictor, blt)

	for child in node.children:
		calculate_blt(node, child, predictor, count_threshold, stdev_threshold, logger)



def main():
	parser = argparse.ArgumentParser(
		description="Calculate Baseline Tolerance statistics")

	cmd = DefaultCommandHelper(parser)

	parser.add_argument("tree_path", metavar="TREE_PATH",
						help="The groups descendant tree")

	parser.add_argument("root_group", metavar="ROOT_GROUP",
						help="Tree root group")

	parser.add_argument("group_genes_path", metavar="GROUP_FEATS_PATH",
						help="Map between groups and features")

	parser.add_argument("stats_path", metavar="STATS_PATH",
						help="Partial feature statistics")

	parser.add_argument("out_path", metavar="OUTPUT_PATH",
						help="Output feature statistics")

	parser.add_argument("--tsv", dest="tsv_path", metavar="PATH",
						help="Store baseline tolerance in tsv format too.")

	parser.add_argument("-c", "--count-threshold", dest="count_threshold", metavar="N", default=DEFAULT_COUNT_THRESHOLD,
						help="Minimum number of features per group")

	parser.add_argument("--stdev-threshold", dest="stdev_threshold", metavar="V", default=DEFAULT_STDEV_THRESHOLD,
						help="Skip feature statistics with a standard deviation less than V (it will be calculated at the level of groups)")

	args, logger = cmd.parse_args("blt-groups")

	logger.info("Loading groups tree ...")

	tree = Tree()
	with tsv.open(args.tree_path) as f:
		for group, children in tsv.lines(f, (str, lambda v: set(v.split(",")))):
			tree.add_node(group, children)

	logger.info("  Nodes: {}".format(tree.node_count))

	logger.info("Loading mappings between groups and features ...")

	all_groups = set()
	all_features = set()
	with tsv.open(args.group_genes_path) as f:
		for group, features in tsv.lines(f, (str, lambda v: set(v.split(",")))):
			tree.add_node(group, features)
			all_groups.add(group)
			all_features.update(features)

	logger.info("  Nodes: {}".format(tree.node_count))
	logger.info("  Groups: {}".format(len(all_groups)))
	logger.info("  Features: {}".format(len(all_features)))

	logger.info("Loading partial statistics ...")

	with tsv.open(args.stats_path) as f:
		predictors = f.readline().rstrip("\n").split("\t")[1:]
		num_predictors = len(predictors)
		num_features = 0
		for line in f:
			try:
				fields = line.rstrip("\n").split("\t")
				feature = fields[0]
				node = tree.get_or_create_node(feature)
				for p, ss in zip(predictors, fields[1:]):
					try:
						s0, s1, s2 = [float(v) if i > 0 else int(v) for i, v in enumerate(ss.split("/"))]
						node.set_pblt(p, PartialBLT(s0, s1, s2, sources=set([feature])))
					except:
						import traceback
						traceback.print_exc()
						logger.warn("Failed to parse partial baseline tolerance"
									" for {}/{} from {}".format(feature, p, ss))
						exit(-1)
						continue
				num_features += 1
			except:
				logger.warn("Failed to parse partial baseline tolerance"
									" for {} from {}".format(feature, line))
				continue

	logger.info("  Nodes: {}".format(tree.node_count))
	logger.info("  Features: {}".format(num_features))
	logger.info("  Predictors: {}".format(", ".join(predictors)))

	logger.info("Calculating baseline tolerance ...")

	for predictor in predictors:
		logger.info("For {} ...".format(predictor))

		calculate_blt(
			parent=None, node=tree.get_or_create_node(args.root_group), predictor=predictor,
			count_threshold=args.count_threshold, stdev_threshold=args.stdev_threshold, logger=logger)

	# TODO log summary info

	logger.info("Writing results into {} ...".format(os.path.basename(args.out_path)))

	if args.tsv_path is not None:
		with tsv.open(args.tsv_path, "w") as of:
			tsv.write_line(of, "FEATURE", *predictors)
			for feature in all_features:
				sb = [feature]
				node = tree.get_node(feature)
				predictors_with_blt = 0
				for predictor in predictors:
					blt = node.get_blt(predictor)
					if blt is None or blt.n < args.count_threshold:
						sb += ["/".join(["-"] * 5)]
						continue

					predictors_with_blt += 1
					sb += ["/".join(map(str, [blt.from_node, blt.scope, blt.n, blt.mean, blt.stdev]))]

				if predictors_with_blt > 0:
					tsv.write_line(of, *sb)

	with tsv.open(args.out_path, "w") as of:
		tree_blt = {}
		for node_name, node in tree.nodes.items():
			predictors_blt = {}
			for predictor in predictors:
				pred_blt = node.get_blt(predictor)
				if pred_blt is None or pred_blt.n < args.count_threshold:
					continue

				predictors_blt[predictor] = dict(
					from_node=pred_blt.from_node, scope=pred_blt.scope,
					N=pred_blt.n, mean=pred_blt.mean, stdev=pred_blt.stdev)

			if len(predictors_blt) > 0:
				tree_blt[node.name] = predictors_blt

		doc = dict(
			created=str(datetime.now()),
			predictors=predictors,
			count_threshold=args.count_threshold,
			stdev_threshold=args.stdev_threshold,
			tree=None, # tree relations
			features=list(all_features),
			pblt=None, # TODO
			blt=tree_blt
		)
		json.dump(doc, of, indent=True)


	return 0

if __name__ == "__main__":
	exit(main())