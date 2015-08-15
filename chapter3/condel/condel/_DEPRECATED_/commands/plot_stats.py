#!/usr/bin/env python

import os
import argparse

from matplotlib import pyplot as plt

from bgcore import logging as bglogging
from condel._DEPRECATED_.weights import load_weights


def arrdiv(arr, cte):
	return [float(v) / cte for v in arr]

def main():
	parser = argparse.ArgumentParser(
		description="Plot training sets statistics")

	parser.add_argument("path", metavar="PATH",
						help="The statistics json file")

	parser.add_argument("-o", dest="out_path", metavar="PATH",
						help="The path to save the plot image.")

	parser.add_argument("-W", "--width", dest="fig_width", metavar="WIDTH", type=int,
						help="The image width.")

	parser.add_argument("-H", "--height", dest="fig_height", metavar="HEIGHT", type=int,
						help="The image height.")

	parser.add_argument("--dpi", dest="fig_dpi", metavar="DPI", type=int, default=100,
						help="The image dpi.")

	parser.add_argument("-p", "--predictors", dest="predictor_names", metavar="NAMES",
						help="The names of the predictors to represent (seppareted by commas).")

	parser.add_argument("-i", "--interactive", dest="interactive", action="store_true", default=False,
						help="Show the plot in interactive mode.")

	bglogging.add_logging_arguments(parser)

	args = parser.parse_args()

	bglogging.initialize(args)

	log = bglogging.get_logger("plot-stats")

	log.info("Loading state from {} ...".format(os.path.basename(args.path)))

	state = load_weights(args.path)

	predictor_names, stats = [state[k] for k in ["predictor_names", "stats"]]

	if args.predictor_names is not None:
		valid_names = set(predictor_names)
		args.predictor_names = [s.strip() for s in args.predictor_names.split(",")]
		predictor_names = [name for name in args.predictor_names if name in valid_names]

		if len(predictor_names) == 0:
			log.error("No scores selected. Please choose between: {}".format(", ".join(valid_names)))
			exit(-1)

	#log.info("Plotting ...")

	fig = plt.figure(figsize=(args.fig_width or 12, args.fig_height or 10.4), dpi=args.fig_dpi or 100)

	alpha = 0.7

	num_predictors = len(predictor_names)
	for i in range(num_predictors):
		predictor_name = predictor_names[i]

		predictor_stats = stats[predictor_name]
		(intervals, dp, dn, cump, cumn, cdp, cdn, tp, tn, fp, fn, mcc, accuracy, cutoff) = [
			predictor_stats[k] for k in [
				"values", "dp", "dn", "cump", "cumn", "cdp", "cdn", "tp", "tn", "fp", "fn", "mcc", "acc", "cutoff"]]

		dax = fig.add_subplot(4, num_predictors, i + 1, title="{}".format(predictor_name))
		cdax = fig.add_subplot(4, num_predictors, 1 * num_predictors + i + 1)
		tfax = fig.add_subplot(4, num_predictors, 2 * num_predictors + i + 1)
		aax = fig.add_subplot(4, num_predictors, 3 * num_predictors + i + 1)

		# distribution
		dax.grid()
		dax.plot(intervals, arrdiv(dp, max(dp)), "r-", alpha=alpha)
		dax.plot(intervals, arrdiv(dn, max(dn)), "b-", alpha=alpha)
		dax.plot([cutoff, cutoff], [0.0, 1.0], "k--")
		dax.legend(('POS', 'NEG'), 'upper center', ncol=2, frameon=False, prop={'size':10})

		# cummulative distribution
		cdax.grid()
		cdax.plot(intervals, arrdiv(cdp, cump), "r-", alpha=alpha)
		cdax.plot(intervals, arrdiv(cdn, cumn), "b-", alpha=alpha)
		cdax.plot([cutoff, cutoff], [0.0, 1.0], "k--")
		cdax.legend(('POS', 'NEG'), 'upper center', ncol=2, frameon=False, prop={'size':10})

		# TP/FN/FP/TN
		tfax.grid()
		tfax.plot(intervals, arrdiv(tp, cump), "r-", alpha=alpha)
		tfax.plot(intervals, arrdiv(fn, cump), "c--", alpha=alpha)
		tfax.plot(intervals, arrdiv(fp, cumn), "b-", alpha=alpha)
		tfax.plot(intervals, arrdiv(tn, cumn), "m--", alpha=alpha)
		tfax.plot([cutoff, cutoff], [0.0, 1.0], "k--")
		tfax.legend(('TP', 'FN', 'FP', 'TN'), 'upper center', ncol=4, frameon=False, prop={'size':8})

		# MCC/Accuracy
		aax.grid()
		aax.plot(intervals, mcc, "g-", alpha=alpha)
		aax.plot(intervals, accuracy, "y-", alpha=alpha)
		aax.plot([cutoff, cutoff], [0.0, 1.0], "k--")
		aax.legend(('MCC', 'Accuracy'), 'upper center', ncol=2, frameon=False, prop={'size':10})

	if args.out_path is not None:
		from matplotlib import pylab
		log.info("Saving image into {} ...".format(os.path.basename(args.out_path)))
		pylab.savefig(args.out_path, bbox_inches=0)

	if args.interactive:
		plt.show()

if __name__ == "__main__":
	main()
