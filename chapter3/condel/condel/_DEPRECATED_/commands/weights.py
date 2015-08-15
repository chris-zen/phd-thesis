#!/usr/bin/env python

import os
import argparse
import json
from math import sqrt
import numpy as np

import pandas as pd
from bgcore import tsv
from bgcore import logging as bglogging
from fannsdb.columns import COORD_COLUMNS
from fannsdb.types import score_value
from condel._DEPRECATED_.weights import save_weights


PREDICTOR_TRANSFORM = dict(
	SIFT=lambda v: 1.0 - v,
	FATHMM=lambda x: -x,
	FATHMMC=lambda x: -x
)

POS_COLUMNS = ["PROTEIN", "AA_POS", "AA_REF", "AA_ALT"]

POS_EVENT = 1
NEG_EVENT = 0

EVENT_TYPES = {
	"+" : POS_EVENT, "P" : POS_EVENT, "D" : POS_EVENT, "POS" : POS_EVENT,
	"-" : NEG_EVENT, "N" : NEG_EVENT, "N" : NEG_EVENT, "NEG" : NEG_EVENT
}

def load_events(f, column_indices, predictors, stats, logger):
	count = [0, 0]
	last_pos = [[None]*4]*2

	id_index = column_indices["ID"]
	pos_indices = [column_indices[name] for name in POS_COLUMNS]
	pred_indices = [column_indices[p] for p in predictors]

	for fields in tsv.rows(f):
		try:
			event_type = EVENT_TYPES[fields[id_index]]
		except KeyError:
			raise Exception("Unknown event type: {}".format(fields[id_index]))

		current_pos = [fields[i] for i in pos_indices]
		if last_pos[event_type] == current_pos:
			continue

		last_pos[event_type] = current_pos

		count[event_type] += 1

		protein, pos, aa_ref, aa_alt = current_pos
		scores = [score_value(fields[pi]) for pi in pred_indices]

		for predictor, score in zip(predictors, scores):
			if score is None or not predictor in stats:
				continue

			if predictor in PREDICTOR_TRANSFORM:
				score = PREDICTOR_TRANSFORM[predictor](score)

			predictor_stats = stats[predictor]
			(rmin, rmax, dim, vmin, vmax, size,
			 dp, dn, tp, tn, fp, fn) = [predictor_stats[k] for k in [
											"rmin", "rmax", "dim", "vmin", "vmax", "size",
											"dp", "dn", "tp", "tn", "fp", "fn"]]

			r = (score - rmin) / dim
			index = int(r * size) if score < rmax else size - 1

			if vmin is None or score < vmin:
				predictor_stats["vmin"] = score
			if vmax is None or score > vmax:
				predictor_stats["vmax"] = score

			if event_type == POS_EVENT:
				dp[index] += 1
				for i in xrange(0, index):
					tp[i] += 1
				for i in xrange(index, size):
					fn[i] += 1

			elif event_type == NEG_EVENT:
				dn[index] += 1
				for i in xrange(0, index):
					fp[i] += 1
				for i in xrange(index, size):
					tn[i] += 1

	return count[POS_EVENT], count[NEG_EVENT]

def main():
	parser = argparse.ArgumentParser(
		description="Calculate weights")

	parser.add_argument("ranges_path", metavar="RANGES_PATH",
						help="JSON file generated with pred-list containing predictors stats. Only min and max are used.")

	parser.add_argument("training_path", metavar="TRAINING_PATH",
						help="The training set scores. ID column should be POS/NEG for positive/negative sets.")

	parser.add_argument("-o", dest="out_path", metavar="OUT_PATH",
						help="The file where weights will be saved. Use - for standard output.")

	parser.add_argument("-p", "--predictors", dest="predictors", metavar="PREDICTORS",
						help="Comma separated list of predictors to fetch")

	parser.add_argument("-P", "--precision", dest="precision", metavar="PRECISSION", type=int, default=3,
						help="Distribution precision")

	parser.add_argument("-f", "--full-state", dest="full_state", action="store_true", default=False,
						help="Save intermediate calculations to allow further exploration and plotting")

	bglogging.add_logging_arguments(parser)

	args = parser.parse_args()

	bglogging.initialize(args)

	logger = bglogging.get_logger("weights")
	
	if args.out_path is None:
		prefix = os.path.splitext(os.path.basename(args.training_path))[0]
		if prefix.endswith("-scores"):
			prefix = prefix[:-7]
		args.out_path = os.path.join(os.getcwd(), "{}-weights.json".format(prefix))

	if args.predictors is not None:
		args.predictors = [p.strip() for p in args.predictors.split(",")]

	logger.info("Loading ranges from {} ...".format(os.path.basename(args.ranges_path)))

	with open(args.ranges_path) as f:
		pred_stats = json.load(f)

	predictor_range = {}
	for pid, pstats in pred_stats.items():
		predictor_range[pid] = (pstats["min"], pstats["max"])

	logger.info("Reading training set {} ...".format(args.training_path if args.training_path != "-" else "from standard input"))

	with tsv.open(args.training_path) as f:

		# Select predictors from the available predictors in the dataset or user selection

		column_names, column_indices = tsv.header(f)
		available_predictors = [c for c in column_names if c not in set(COORD_COLUMNS)]
		if args.predictors is None:
			predictors = available_predictors
		else:
			missing_predictors = [p for p in args.predictors if p not in set(available_predictors)]
			if len(missing_predictors) > 0:
				logger.error("Missing predictors: {}".format(", ".join(missing_predictors)))
				exit(-1)
			predictors = args.predictors

	data = pd.read_csv(args.training_path, sep="\t", index_col=False,
					   usecols=["ID"] + predictors,
					   true_values=["POS"], false_values=["NEG"])

	data.rename(columns={"ID" : "EVT"}, inplace=True)

	# Initialize statistics

	logger.info("Initializing metrics ...")

	step = 1.0 / 10**args.precision

	stats = dict()

	state = dict(
		predictor_names = predictors,
		precision = args.precision,
		step = step,
		stats = stats)

	for predictor in predictors:
		d = data[["EVT", predictor]]
		d = d[np.isfinite(d.iloc[:, 1])]

		nump = d.iloc[:, 0].sum()
		numn = d.shape[0] - nump

		rmin, rmax = d.iloc[:, 1].min(), d.iloc[:, 1].max()

		dim = rmax - rmin
		size = int(dim / step) + 1
		values = [(x * step) + rmin for x in xrange(size)]

		logger.info("  {:10}: p={}, n={}, min={}, max={}, bins={}".format(predictor, nump, numn, rmin, rmax, size))

		stats[predictor] = dict(
			rmin = rmin,
			rmax = rmax,
			dim = dim,
			values = values,
			size = size,
			vmin = rmin,
			vmax = rmax,
			dp = [0] * size,
			dn = [0] * size,
			cdp = [0] * size,
			cdn = [0] * size,
			cump = 0,
			cumn = 0,
			tp = [0] * size,
			tn = [0] * size,
			fp = [0] * size,
			fn = [0] * size,
			mcc = [0] * size,
			acc = [0] * size,
			auc = [0] * size,
			cutoff = None,
			cutoff_index = None,
			cutoff_mcc = None,
			cutoff_acc = None,
			cutoff_auc = None)

	positive_count = data.iloc[:, 0].sum()
	negative_count = data.shape[0] - positive_count

	logger.info("  TOTAL     : positive={}, negative={}".format(positive_count, negative_count))

	logger.info("Calculating scores distribution and confusion matrices ...")



	logger.info("Calculating cumulative distribution ...")

	for predictor in predictors:
		predictor_stats = stats[predictor]
		dp, dn, cdp, cdn = [predictor_stats[k] for k in ["dp", "dn", "cdp", "cdn"]]
		cump = 0
		cumn = 0
		i = len(dp) - 1
		while i >= 0:
			cdp[i] = dp[i] + cump
			cump += dp[i]

			cdn[i] = dn[i] + cumn
			cumn += dn[i]

			i -= 1

		predictor_stats["cump"] = cump
		predictor_stats["cumn"] = cumn

		logger.info("  {}: cump={}, cumn={}".format(predictor, cump, cumn))

	logger.info("Calculating accuracy and cutoff ...")

	for predictor in predictors:
		predictor_stats = stats[predictor]
		values, size, tp, tn, fp, fn, mcc, acc = [predictor_stats[k] for k in [
													"values", "size", "tp", "tn", "fp", "fn", "mcc", "acc"]]

		cutoff = -1
		cutoff_index = -1
		best_mcc = -1e6
		for i in xrange(size):
			try:
				#http://en.wikipedia.org/wiki/Matthews_correlation_coefficient
				mcc[i] = (tp[i] * tn[i] - fp[i] * fn[i]) / sqrt((tp[i] + fp[i]) * (tp[i] + fn[i]) * (tn[i] + fp[i]) * (tn[i] + fn[i]))

				#http://en.wikipedia.org/wiki/Accuracy
				acc[i] = (tp[i] + tn[i]) / float(tp[i] + fp[i] + fn[i] + tn[i])
			except ZeroDivisionError:
				mcc[i] = 0
				acc[i] = 0

			if mcc[i] > best_mcc:
				cutoff = values[i]
				cutoff_index = i
				best_mcc = mcc[i]

		best_acc = max(acc)

		predictor_stats["cutoff"] = cutoff
		predictor_stats["cutoff_index"] = cutoff_index
		predictor_stats["cutoff_mcc"] = best_mcc
		predictor_stats["cutoff_acc"] = best_acc

		logger.info("  {}: cutoff={:.3f}, mcc={:.2f}, accuracy={:.2f}".format(
			predictor, cutoff, best_mcc * 100.0, best_acc * 100.0))

	if args.full_state:
		logger.info("Saving weights with full state ...")

		out_path = args.out_path
		save_weights(out_path, state)

	else:
		logger.info("Saving weights ...")

		stats = {}

		reduced_state = dict(
			predictor_names=state["predictor_names"],
			precision=state["precision"],
			step=state["step"],
			stats=stats)

		for predictor in state["predictor_names"]:
			predictor_stats = state["stats"][predictor]
			stats[predictor] = dict(
				rmin=predictor_stats["rmin"],
				rmax=predictor_stats["rmax"],
				dim=predictor_stats["dim"],
				values=predictor_stats["values"],
				size=predictor_stats["size"],
				cdp=predictor_stats["cdp"],
				cdn=predictor_stats["cdn"],
				cutoff=predictor_stats["cutoff"],
				cutoff_index=predictor_stats["cutoff_index"])

		save_weights(args.out_path, reduced_state)

	return 0

if __name__ == "__main__":
	exit(main())
