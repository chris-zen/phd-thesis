#!/usr/bin/env python

import os
import logging
from datetime import datetime as dt

from bgcore import tsv
from fannsdb.mutations.mutation import Mutation
from fannsdb.mutations.parser import DnaAndProtMutationParser, PrematureEnd, UnexpectedToken
from fannsdb.columns import COORD_COLUMNS
from fannsdb.utils import RatedProgress

STATE_LINE_NUM = "line_num"
STATE_LINE = "line"
STATE_MUTATION = "mutation"
STATE_HITS = "hits"
STATE_FAILS = "fails"

def fetch_iter(db, muts_path, maps=None, predictors=None, muts_header=False, state=None, logger=None):
	"""
	Iterator that fetches scores from the database from the mutations in a file.
	
	:param db: FannsDb interface.
	:param muts_path: The input path for mutations.
	:param maps: Map transcript/protein ensembl identifiers with external identifiers (swissprot_id, ...)
	:param predictors: Predictors for which to obtain the scores.
	:param muts_header: Whether the muts_path has a header or not.
	:param state: The state of the iteration: hits, fails.
	:param logger: Logger to use. If not specified a new one is created.
	"""

	def query_mutation(logger, db, mut, maps, predictors):

		if mut.coord == Mutation.GENOMIC:
			if logger.isEnabledFor(logging.DEBUG):
				logger.debug("  Querying {} {} {} {} {} {} {} ...".format(
					mut.chr, mut.start, mut.end or "*", mut.ref or "*", mut.alt, mut.strand or "*", mut.identifier or "*"))

			for row in db.query_scores(chr=mut.chr, start=mut.start,
											ref=mut.ref, alt=mut.alt, strand=mut.strand,
											predictors=predictors, maps=maps):
				yield row

		elif mut.coord == Mutation.PROTEIN:
			if logger.isEnabledFor(logging.DEBUG):
				logger.debug("  Querying {} {} {} {} {} ...".format(
					mut.protein, mut.start, mut.ref or "*", mut.alt, mut.identifier or "*"))

			for row in db.query_scores(protein=mut.protein, aa_pos=mut.start, aa_ref=mut.ref, aa_alt=mut.alt,
											predictors=predictors, maps=maps):
				yield row

		else:
			logger.warn("Unknown coordinates system: {}".format(mut.line))

	if logger is None:
		logger = logging.getLogger("fannsdb.fetch")

	state = state if state is not None else {}
	state[STATE_HITS] = state[STATE_FAILS] = 0
	maps = maps if maps is not None else []
	predictors = predictors if predictors is not None else []
	
	logger.info("Reading {} ...".format(os.path.basename(muts_path) if muts_path != "-" else "from standard input"))

	progress = RatedProgress(logger, name="SNVs")

	with tsv.open(muts_path) as f:
		if muts_header:
			tsv.skip_comments_and_empty(f) # this returns the first non empty nor comment line (the header)

		mutparser = DnaAndProtMutationParser()
		for line_num, line in enumerate(f, start=1):
			line = line.rstrip(" \n\r")
			if len(line) == 0 or line.startswith("#"):
				continue

			try:
				mut = mutparser.parse(line)
			except PrematureEnd:
				logger.error("Missing fields at line {}".format(line_num))
				state[STATE_FAILS] += 1
				continue
			except UnexpectedToken as ex:
				logger.error("Unexpected field '{}' at line {}".format(ex.args[0], line_num))
				state[STATE_FAILS] += 1
				continue

			state.update({
				STATE_LINE_NUM : line_num,
				STATE_LINE : line,
				STATE_MUTATION : mut})

			exists = False
			for row in query_mutation(logger, db, mut, maps, predictors):
				exists = True

				yield row

			progress.update()

			if exists:
				state[STATE_HITS] += 1
			else:
				state[STATE_FAILS] += 1

	progress.log_totals()

	hits, fails = [state[k] for k in [STATE_HITS, STATE_FAILS]]
	logger.info("Finished. total={}, hits={}, fails={}, elapsed={}".format(hits + fails, hits, fails, progress.elapsed_time))


def fetch(db, muts_path, out_path, params=None, columns=None, maps=None, predictors=None,
		  labels=None, calc_labels=None, muts_header=False, logger=None):
	
	params = params or {}
	columns = columns or [c.lower() for c in COORD_COLUMNS]
	maps = maps or []
	predictors = predictors or []
	labels = labels or []
	
	state = {}
	
	with tsv.open(out_path, "w") as wf:
		
		metadata = db.metadata
		if "version" in metadata:
			tsv.write_param(wf, "db-version", db.metadata["version"])
		tsv.write_param(wf, "fetched", dt.now().strftime("%Y-%m-%d %H:%M:%S"))
		for k, v in params.items():
			tsv.write_param(wf, k, v)
	
		tsv.write_line(wf, "ID", *[c.upper() for c in columns] + [m.upper() for m in maps] + predictors + labels)
	
		for row in fetch_iter(db, muts_path, maps=maps, predictors=predictors,
							  muts_header=muts_header, state=state, logger=logger):
			
			if calc_labels is not None:
				labels = calc_labels(row) or {}
			else:
				labels = {}
	
			xrefs = row["xrefs"]
			scores = row["scores"]

			tsv.write_line(wf, state[STATE_MUTATION].identifier,
				   *[row[c] for c in columns]
				   + [xrefs[m] for m in maps]
				   + [scores[p] for p in predictors]
				   + [labels.get(l, "") for l in labels])
	
	return {k : state[k] for k in [STATE_HITS, STATE_FAILS]}