#!/usr/bin/env python

import os
import json
import argparse

import numpy as np
from matplotlib import pyplot as plt

from fannsdb.cmdhelper import Command

def main():
	parser = argparse.ArgumentParser(
		description="Calculate TransFIC for the selected scores")

	cmd = Command(parser)

	parser.add_argument("weights", metavar="WEIGHTS_PATH", nargs="+",
						help="The list of files containing weights.")

	parser.add_argument("-c", dest="comparisons", metavar="S1/S2", action="append",
						help="Compare score S1 with S2")

	parser.add_argument("-o", dest="out_path", metavar="PATH",
						help="The path to save the plot image.")

	parser.add_argument("-W", "--width", dest="fig_width", metavar="WIDTH", type=int,
						help="The image width.")

	parser.add_argument("-H", "--height", dest="fig_height", metavar="HEIGHT", type=int,
						help="The image height.")

	parser.add_argument("--dpi", dest="fig_dpi", metavar="DPI", type=int, default=100,
						help="The image dpi.")

	parser.add_argument("-i", "--interactive", dest="interactive", action="store_true", default=False,
						help="Show the plot in interactive mode.")

	parser.add_argument("-t", "--title", dest="title", metavar="TITLE",
						help="The plot title.")

	args, logger = cmd.parse_args("perf-plot")

	try:
		width = 0.5

		if args.comparisons is None:
			raise Exception("Select the predictors to compare with -c please.")

		comparisons = []
		for c in args.comparisons:
			s = c.split("/")
			if len(s) != 2:
				raise Exception("Wrong comparison format: {}".format(c))
			comparisons += [tuple(s)]

		num_comparisons = len(comparisons)

		if not args.interactive:
			import matplotlib
			matplotlib.use('Agg')

		from matplotlib import pylab
		#pylab.rcParams['xtick.major.pad'] = '8'
		pylab.rcParams['ytick.major.pad'] = '20'

		fig = plt.figure(figsize=(args.fig_width or 12, args.fig_height or 10.4), dpi=args.fig_dpi or 100)
		fig.subplots_adjust(left=0.11, bottom=0.03, right=0.99, top=0.94, wspace=0.07, hspace=0.53)
		if args.title is not None:
			fig.suptitle(args.title)

		num_rows = len(args.weights)
		for row_idx, wpath in enumerate(args.weights, start=0):
			basename = os.path.basename(wpath)
			name = basename
			if name.endswith(".json"):
				name = name[:-5]
			if name.endswith("-weights"):
				name = name[:-8]

			i = name.find("__")
			if i > 0:
				name1, name2 = name.split("__")[:2]
			else:
				name1 = name2 = name

			logger.info("{} ...".format(name))

			with open(wpath) as f:
				state = json.load(f)

			metrics = state["metrics"]

			x = np.arange(0, 100, 10)
			y = np.arange(2)

			j = 0
			for p1, p2 in comparisons:

				if p1 not in metrics:
					raise Exception("Predictor '{}' not found in statistics file {}".format(p1, basename))

				if p2 not in metrics:
					raise Exception("Predictor '{}' not found in statistics file {}".format(p2, basename))

				stats1 = metrics[p1]
				stats2 = metrics[p2]

				mcc1 = stats1["best_perf"]["MCC"] * 100.0
				mcc2 = stats2["best_perf"]["MCC"] * 100.0

				row_title = "{}\n{}".format(name1, name2)
				col_title = p1 if row_idx == 0 else ""

				ax = fig.add_subplot(num_rows, num_comparisons, row_idx * num_comparisons + j + 1, title=col_title)
				ax.set_xticks(x)
				ax.set_xlim(0, 100)
				ax.xaxis.grid(True)
				ax.set_yticks([0.25, 0.75])
				if j == 0:
					ax.set_ylabel(row_title, rotation=90)
					ax.set_yticklabels(["Orig", "TFIC"])
				else:
					ax.set_yticklabels(["", ""])
				b1 = ax.barh([0.0], [mcc1], width, color="r")
				b2 = ax.barh([0.5], [mcc2], width, color="y")

				j += 1

			#ax.set_xticklabels(tuple([p1 for p1, p2 in comparisons]))
			#ax.legend((b1[0], b2[0]), ("Original score", "TransFIC score"))

		if args.out_path is not None:
			plt.savefig(args.out_path, bbox_inches=0)

		if args.interactive:
			plt.show()
	except:
		cmd.handle_error()

	return 0

if __name__ == "__main__":
	exit(main())