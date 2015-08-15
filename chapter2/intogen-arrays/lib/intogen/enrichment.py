import sys
import os
import os.path
import subprocess
import shutil
from tempfile import mkdtemp
from intogen.io import FileReader, FileWriter
from intogen import tdm, tsv

class EmptyResults(Exception):
	pass

def enrichment(log, conf, rs, data_repo, results_path, data_file, e, ec,
				filtered_columns, filtered_columns_new_names):

	eid = e["id"]

	key = (e["study_id"], e["platform_id"], e["icdo_topography"], e["icdo_morphology"])

	# determine the modules file
	mod_repo, mod_path = rs.from_url(ec["modules_file"])
	mod_local_path = mod_repo.get_local(mod_path)

	# oncodrive data file
	matrix_repo, matrix_path = rs.from_url(data_file)
	matrix_local_path = matrix_repo.get_local(matrix_path)

	e["data_file"] = data_file
	e["modules_file"] = ec["modules_file"]

	results_local_path = None

	tmp_path = mkdtemp(prefix = "enrichment_")
	log.debug("Temporary directory: {}".format(tmp_path))

	valid = True

	try:
		log.info("Filtering pvalue columns from {} ...".format(data_file))

		# filter columns for pvalues
		data_local_path = os.path.join(tmp_path, "data.tsv")

		rf = of = None
		try:
			rf = FileReader(matrix_local_path)
			of = FileWriter(data_local_path)
			row_count = tsv.filter_columns(rf, of,
					filtered_columns, filtered_columns_new_names)
		finally:
			if rf is not None:
				rf.close()
			if of is not None:
				of.close()

		if row_count == 0:
			log.warn("Oncodrive results are empty: {}".format(matrix_path))
			raise EmptyResults

		# apply background if necessary
		if "population.file" in ec:
			pop_url = ec["population.file"]
			pop_missing_value = ec.get("population.missing_value", "-")
			log.info("Applying background from {} with missing value {} ...".format(pop_url, pop_missing_value))
			data2_local_path = os.path.join(tmp_path, "data-filtered.tsv")
			pop_repo, pop_path = rs.from_url(pop_url)
			pop_local_path = pop_repo.get_local(pop_path)
			cmd = " ".join([
				conf["bin_paths.python"], conf["bin_paths.matrix_background"],
				"--verbose --missing-value", pop_missing_value,
				"-o", data2_local_path,
				data_local_path, pop_local_path ])

			log.debug(cmd)
			retcode = subprocess.call(args = cmd, shell = True)

			if retcode != 0:
				raise Exception("Applying population background for ({}) [{}] failed with code {}".format(", ".join(key), eid, retcode))

			pop_repo.close_local(pop_local_path)
			data_local_path = data2_local_path

		# enrichment results
		e["results_file"] = data_repo.url(results_path)
		results_local_path = data_repo.create_local(results_path)

		log.info("Running enrichment ...")
		log.debug("\tData file: {}".format(data_local_path))
		log.debug("\tModules file: {}".format(ec["modules_file"]))

		gitools_enrichment_bin = os.path.join(conf["bin_paths.gitools"], "bin", "gitools-enrichment")

		sb = [ gitools_enrichment_bin,
			"-N", eid, "-w", tmp_path, "-p 1",
			"-mf tcm", "-m", mod_local_path,
			"-df cdm", "-d", data_local_path,
			"-t", ec["test"] ]

		if "filter" in ec:
			sb += ["-b", ec["filter"]]

		if ec.get("only_mapped_items", False, dtype=bool):
			sb += ["-only-mapped-items"]

		#if "population" in ec:
		#	pop_repo, pop_path = rs.from_url(ec["population"])
		#	pop_local_path = pop_repo.get_local(pop_path)
		#	sb += ["-P", pop_local_path]

		cmd = " ".join(sb)

		log.debug(cmd)

		retcode = subprocess.call(args = cmd, shell = True)

		sys.stdout.write("\n")
		sys.stdout.flush()

		if retcode != 0:
			raise Exception("Enrichment for ({}) [{}] failed with code {}".format(", ".join(key), eid, retcode))

		# flatten results

		log.info("Flattening results into {} ...".format(e["results_file"]))

		try:
			gitools_results = os.path.join(tmp_path, eid + "-results.tdm.gz")
			rf = FileReader(gitools_results)
			of = FileWriter(results_local_path)
			tdm.flatten(rf, of,
				{ "column" : str, "row" : str, "N" : int, "observed" : int,
				"expected-mean" : float, "expected-stdev" : float, "probability" : float,
				"right-p-value" : float, "corrected-right-p-value" : float },

				["N", "observed", "expected-mean", "expected-stdev",
				"probability", "right-p-value", "corrected-right-p-value"])
		finally:
			if rf is not None:
				rf.close()
			if of is not None:
				of.close()

		# close local paths
		data_repo.put_local(results_local_path)

	except EmptyResults:
		valid = False

	except Exception as ex:
		log.exception(ex)

		if results_local_path is not None:
			data_repo.close_local(results_local_path)

		valid = False

	finally:
		shutil.rmtree(tmp_path)
		mod_repo.close_local(mod_local_path)
		data_repo.close_local(matrix_local_path)
		#if "population" in ec:
		#	pop_repo.close_local(pop_local_path)

	return valid
