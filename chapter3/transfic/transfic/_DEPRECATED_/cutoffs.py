#!/usr/bin/env python

import os
import argparse
import json

from bgcore import tsv
from fannsdb.columns import COORD_COLUMNS
from fannsdb.types import score_value
from condel._DEPRECATED_.weights import save_weights
from transfic.cmdhelper import DefaultCommandHelper


POS_HEADERS = ["PROTEIN", "AA_POS", "AA_REF", "AA_ALT"]

HIGH_REC_EVENT = 1
NON_REC_EVENT = 0

EVENT_TYPES = {
	"H" : HIGH_REC_EVENT, "HR" : HIGH_REC_EVENT, "HIGH" : HIGH_REC_EVENT, "POS" : HIGH_REC_EVENT,
	"N" : NON_REC_EVENT, "NR" : NON_REC_EVENT, "NON" : NON_REC_EVENT, "NEG" : NON_REC_EVENT
}

def load_events(f, column_indices, predictors, transforms, stats, logger):
	count = [0, 0]
	last_pos = [[None]*4]*2

	id_index = column_indices["ID"]
	pos_indices = [column_indices[name] for name in POS_HEADERS]

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
		scores = [score_value(fields[column_indices[p]]) for p in predictors]

		for predictor, score in zip(predictors, scores):
			if score is None or not predictor in stats:
				continue

			if predictor in transforms:
				for expr, func in transforms[predictor]:
					try:
						score = func(score)
					except:
						logger.error("Error applying transformation {} to score {}".format(expr, score))

			predictor_stats = stats[predictor]
			(rmin, rmax, dim, vmin, vmax, size, dp, dn) = [predictor_stats[k] for k in [
											"rmin", "rmax", "dim", "vmin", "vmax", "size", "dp", "dn"]]

			r = (score - rmin) / dim
			index = int(r * size) if score < rmax else size - 1

			if vmin is None or score < vmin:
				predictor_stats["vmin"] = score
			if vmax is None or score > vmax:
				predictor_stats["vmax"] = score

			if event_type == HIGH_REC_EVENT:
				dp[index] += 1
			elif event_type == NON_REC_EVENT:
				dn[index] += 1

	return { "high_recurrent" : count[HIGH_REC_EVENT], "non_recurrent" : count[NON_REC_EVENT] }

def main():
	parser = argparse.ArgumentParser(
		description="Calculate TransFIC cutoffs")

	cmd = DefaultCommandHelper(parser)

	parser.add_argument("ranges_path", metavar="RANGES_PATH",
						help="JSON file generated with pred-list containing predictors stats. Only min and max are used.")

	parser.add_argument("scores_path", metavar="SCORES_PATH",
						help="The dataset with scores for non recurrent and highly recurrent. ID column should be NON/HIGH for non-rec/highly-rec datasets.")

	parser.add_argument("-o", dest="out_path", metavar="OUT_PATH",
						help="The file where cutoffs will be saved. Use - for standard output.")

	cmd.add_selected_predictors_args()

	parser.add_argument("-P", "--precision", dest="precision", metavar="PRECISION", type=int, default=3,
						help="Distribution precision")

	cmd.add_transform_args()

	args, logger = cmd.parse_args("cutoffs")

	if args.out_path is None:
		prefix = os.path.splitext(os.path.basename(args.scores_path))[0]
		if prefix.endswith("-scores"):
			prefix = prefix[:-7]
		args.out_path = os.path.join(os.getcwd(), "{}-cutoffs.json".format(prefix))

	try:
		logger.info("Loading ranges from {} ...".format(os.path.basename(args.ranges_path)))

		with open(args.ranges_path) as f:
			pred_stats = json.load(f)

		predictor_range = {}
		for pid, pstats in pred_stats.items():
			predictor_range[pid] = (pstats["min"], pstats["max"])

		transforms = cmd.get_transforms()

		logger.info("Reading datasets {} ...".format(args.scores_path if args.scores_path != "-" else "from standard input"))

		with tsv.open(args.scores_path) as f:

			# Select predictors from the available predictors in the dataset or user selection

			column_names, column_indices = tsv.header(f)
			excluded_columns = set(COORD_COLUMNS) | set(["ID"])
			available_predictors = [c for c in column_names if c not in excluded_columns]
			predictors = cmd.get_selected_predictors(available_predictors)

			# Initialize statistics

			step = 1.0 / 10**args.precision

			stats = dict()

			state = dict(
				predictors = predictors,
				stats = stats,
				transforms=dict([(p, [e for e, _ in t]) for p, t in transforms.items()]),
				precision = args.precision,
				step = step)

			for predictor in predictors:
				rmin, rmax = predictor_range[predictor] if predictor in predictor_range else (0.0, 1.0)
				dim = rmax - rmin
				size = int(dim / step) + 1
				values = [(x * step) + rmin for x in xrange(size)]

				stats[predictor] = dict(
					rmin = rmin,
					rmax = rmax,
					dim = dim,
					values = values,
					size = size,
					vmin = None,
					vmax = None,
					dp = [0] * size,
					dn = [0] * size,
					cdp = [0] * size,
					cdn = [0] * size,
					cump = 0,
					cumn = 0,
					cutoff = None,
					cutoff_index = None)

			counts = load_events(f, column_indices, predictors, transforms, stats, logger)

			logger.info("  {}".format(", ".join(["{}={}".format(n, c) for n, c in counts.items()])))

		logger.info("Calculating cumulative distribution ...")

		for predictor in predictors:
			predictor_stats = stats[predictor]
			dp, dn, cdp, cdn = [predictor_stats[k] for k in ["dp", "dn", "cdp", "cdn"]]
			cump = 0
			cumn = 0
			i = len(dp) - 1
			while i >= 0:
				#cdp[i] = dp[i] + cump
				cump += dp[i]
				cdp[i] = cump

				cdn[i] = dn[i] + cumn
				cumn += dn[i]

				i -= 1

			predictor_stats["cump"] = cump
			predictor_stats["cumn"] = cumn

			logger.info("  {}: cump={}, cumn={}".format(predictor, cump, cumn))

		logger.info("Calculating cutoffs ...")

		for predictor in predictors:
			predictor_stats = stats[predictor]
			values, size, vmin, vmax, cump, cumn, cdp, cdn = [predictor_stats[k] for k in [
				"values", "size", "vmin", "vmax", "cump", "cumn", "cdp", "cdn"]]

			cutoff_low_mid_index = -1
			i = 0
			while (i < size) and (cdp[i] / float(cump) >= 0.95):
				cutoff_low_mid_index = i
				i += 1

			cutoff_low_mid = values[cutoff_low_mid_index]
			predictor_stats["cutoff_low_mid"] = cutoff_low_mid
			predictor_stats["cutoff_low_mid_index"] = cutoff_low_mid_index

			cutoff_mid_high_index = -1
			i = 0
			while (i < size) and (cdn[i] / float(cumn) >= 0.20):
				cutoff_mid_high_index = i
				i += 1

			cutoff_mid_high = values[cutoff_mid_high_index]
			predictor_stats["cutoff_mid_high"] = cutoff_mid_high
			predictor_stats["cutoff_mid_high_index"] = cutoff_mid_high_index

			logger.info("  {}: cutoffs: vmin={}, low_mid={}, mid_high={}, vmax={}".format(predictor, vmin, cutoff_low_mid, cutoff_mid_high, vmax))

		logger.info("Saving state ...")

		out_path = args.out_path
		save_weights(out_path, state)

	except:
		cmd.handle_error()

	return 0

if __name__ == "__main__":
	exit(main())
