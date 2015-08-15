#!/usr/bin/env python

import argparse

from matplotlib import pyplot as plt

from bgcore import logging as bglogging
from condel._DEPRECATED_.weights import load_weights

def main():
	parser = argparse.ArgumentParser(
		description="Plot training sets statistics")

	parser.add_argument("path", metavar="PATH",
						help="The statistics json file")

	parser.add_argument("-o", dest="out_path", metavar="PATH",
						help="The path to save the plot image.")

	parser.add_argument("-p", "--predictors", dest="predictor_names", metavar="NAMES",
						help="The names of the predictors to represent (seppareted by commas).")

	parser.add_argument("-i", "--interactive", dest="interactive", action="store_true", default=False,
						help="Show the plot in interactive mode.")

	bglogging.add_logging_arguments(parser)

	args = parser.parse_args()

	bglogging.initialize(args)

	log = bglogging.get_logger("plot-stats")

	log.info("Loading state ...")

	state = load_weights(args.path)

	predictor_names, stats = [state[k] for k in ["predictor_names", "stats"]]

	if args.predictor_names is not None:
		valid_names = set(predictor_names)
		args.predictor_names = [s.strip() for s in args.predictor_names.split(",")]
		predictor_names = [name for name in args.predictor_names if name in valid_names]

		if len(predictor_names) == 0:
			log.error("No scores selected. Please choose between: {}".format(", ".join(valid_names)))
			exit(-1)

	log.info("Plotting ...")

	fig = plt.figure()
	ax = fig.add_subplot(111)
	ax.grid()
	ax.set_xlabel("False Positive Rate (1 - especificity)")
	ax.set_ylabel("True Positive Rate (sensitivity)")
	
	num_predictors = len(predictor_names)
	for predictor_name in predictor_names:
		predictor_stats = stats[predictor_name]
		(size, tp, tn, fp, fn) = [predictor_stats[k] for k in ["size", "tp", "tn", "fp", "fn"]]
		
		tpr = [1.0] * (size + 1)
		fpr = [1.0] * (size + 1)
		for i in range(size):
			tpr[i + 1] = (float(tp[i]) / (tp[i] + fn[i]))
			fpr[i + 1] = (float(fp[i]) / (fp[i] + tn[i]))

		ax.plot(fpr, tpr, "-")
	
	ax.legend(tuple(predictor_names), "lower right", shadow=False)

	ax.plot([0.0, 1.0], [0.0, 1.0], "--", color="0.75")

	if args.out_path is not None:
		from matplotlib import pylab
		pylab.savefig(args.out_path, bbox_inches=0)

	if args.interactive:
		plt.show()

if __name__ == "__main__":
	main()
