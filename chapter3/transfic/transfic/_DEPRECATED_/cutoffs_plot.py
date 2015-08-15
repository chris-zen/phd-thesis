#!/usr/bin/env python

import argparse

from matplotlib import pyplot as plt

from condel._DEPRECATED_.weights import load_weights
from transfic.cmdhelper import DefaultCommandHelper

def main():
	parser = argparse.ArgumentParser(
		description="Plot cutoffs")

	cmd = DefaultCommandHelper(parser)

	parser.add_argument("path", metavar="PATH",
						help="The statistics json file")

	parser.add_argument("-o", dest="out_path", metavar="PATH",
						help="The path to save the plot image.")

	cmd.add_selected_predictors_args()

	parser.add_argument("-i", "--interactive", dest="interactive", action="store_true", default=False,
						help="Show the plot in interactive mode.")

	args, logger = cmd.parse_args("plot-cutoffs")

	logger.info("Loading state ...")

	state = load_weights(args.path)

	available_predictors, stats = [state[k] for k in ["predictors", "stats"]]

	predictors = cmd.get_selected_predictors(available_predictors)

	logger.info("Plotting ...")

	fig = plt.figure(figsize=(12.4, 10.5), dpi=100)
	fig.subplots_adjust(left=0.06, bottom=0.03, right=0.99, top=0.96, wspace=0.22, hspace=0.15)

	num_predictors = len(predictors)
	for i, predictor in enumerate(predictors):

		predictor_stats = stats[predictor]
		(intervals, vmin, vmax, dp, dn, cump, cumn, cdp, cdn, cutoff_low_mid, cutoff_mid_high) = [predictor_stats[k] for k in [
			"values", "vmin", "vmax", "dp", "dn", "cump", "cumn", "cdp", "cdn", "cutoff_low_mid", "cutoff_mid_high"]]

		dax = fig.add_subplot(2, num_predictors, i + 1, title="{}".format(predictor))
		cdax = fig.add_subplot(2, num_predictors, 1 * num_predictors + i + 1)

		dax.grid()
		dax.set_xlim(vmin, vmax)
		dax.plot(intervals, dp, "r-", alpha=0.5)
		dax.plot(intervals, dn, "b-", alpha=0.5)
		dax.plot([cutoff_low_mid, cutoff_low_mid], [0.0, max(dp + dn)], "k--")
		dax.plot([cutoff_mid_high, cutoff_mid_high], [0.0, max(dp + dn)], "k--")
		dax.axvspan(vmin, cutoff_low_mid, facecolor='g', alpha=0.3)
		dax.axvspan(cutoff_low_mid, cutoff_mid_high, facecolor='y', alpha=0.3)
		dax.axvspan(cutoff_mid_high, vmax, facecolor='r', alpha=0.3)
		dax.legend(('HIGH-REC', 'NON-REC'), 'upper center', ncol=2, frameon=False, prop={'size':10})

		cdax.grid()
		cdax.set_xlim(vmin, vmax)
		cdax.plot(intervals, [v / float(cump) for v in cdp], "r-")
		cdax.plot(intervals, [v / float(cumn) for v in cdn], "b-")
		cdax.plot([cutoff_low_mid, cutoff_low_mid], [0.0, 1.0], "k--")
		cdax.plot([cutoff_mid_high, cutoff_mid_high], [0.0, 1.0], "k--")
		cdax.axvspan(vmin, cutoff_low_mid, facecolor='g', alpha=0.3)
		cdax.axvspan(cutoff_low_mid, cutoff_mid_high, facecolor='y', alpha=0.3)
		cdax.axvspan(cutoff_mid_high, vmax, facecolor='r', alpha=0.3)
		cdax.legend(('HIGH-REC', 'NON-REC'), 'upper center', ncol=2, frameon=False, prop={'size':10})

	if args.out_path is not None:
		from matplotlib import pylab
		pylab.savefig(args.out_path, bbox_inches=0)

	if args.interactive:
		plt.show()

if __name__ == "__main__":
	main()
