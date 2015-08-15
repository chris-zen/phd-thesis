import os
import logging

def tfic_calc(feature_stats, scores, predictors, updated_predictors, transforms):
	tfic_scores = {}
	for predictor in predictors:
		upd_pred = updated_predictors[predictor]
		#tfic_scores[upd_pred] = None

		pred_stats = feature_stats.get(predictor)

		if pred_stats is None:
			continue

		score = scores[predictor]
		if score is None:
			continue

		if predictor in transforms:
			for name, func in transforms[predictor]:
				try:
					score = func(score)
				except:
					raise Exception("Error transforming the {} score {} with {}".format(predictor, score, name))

		mean, sd = pred_stats["mean"], pred_stats["stdev"]

		tfic_scores[upd_pred] = (score - mean) / sd

	return tfic_scores

def tfic_calc_file(ds_path, out_path, predictors, updated_predictors, feature_column, blt_stats, transforms, logger=None):
	def parse_float(s):
		try:
			return float(s)
		except:
			return None

	logger = logger or logging.getLogger("tfic-calc-file")

	logger.info("Calculating TransFIC for {} ...".format(os.path.basename(ds_path)))

	with open(ds_path) as f, open(out_path, "w") as wf:
		columns = f.readline().rstrip("\n").split("\t")
		wf.write("\t".join(columns + updated_predictors) + "\n")

		hdr = {n : i for i, n in enumerate(columns)}
		pidx = [(p, hdr[p]) for p in predictors if p in hdr]
		fidx = hdr[feature_column]

		upd_pred = {p : up for p, up in zip(predictors, updated_predictors)}

		rows_count = updated_count = 0
		for rows_count, line in enumerate(f, start=1):
			fields = line.rstrip("\n").split("\t")

			scores = {p : parse_float(fields[ix]) for p, ix in pidx}

			feature = fields[fidx]
			if feature not in blt_stats:
				continue

			feature_stats = blt_stats[feature]

			tfic_scores = tfic_calc(feature_stats, scores, predictors, upd_pred, transforms)

			if len(tfic_scores) > 0:
				updated_count += 1
				wf.write("\t".join(fields + [str(tfic_scores.get(p, "")) for p in updated_predictors]) + "\n")

	logger.info("Done: {} rows, {} updates".format(rows_count, updated_count))
