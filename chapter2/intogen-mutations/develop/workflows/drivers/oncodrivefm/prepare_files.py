import os

from collections import defaultdict

from wok.task import task

from bgcore import tsv

from intogensm.config import GlobalConfig, PathsConfig
from intogensm.projects.db import ProjectDb
from intogensm.projects.results import ProjectResults
from intogensm.oncodrivefm import OncodriveFm

@task.foreach()
def prepare_files(project):
	log = task.logger
	conf = task.conf

	projects_out_port = task.ports("projects_out")

	project_id = project["id"]
	log.info("--- [{0}] --------------------------------------------".format(project_id))

	config = GlobalConfig(conf)
	paths = PathsConfig(config) # avoid that project conf override path configurations
	config = GlobalConfig(conf, project["conf"])

	ofm = OncodriveFm(config.oncodrivefm, paths, log)

	project_results = ProjectResults(project)

	log.info("Retrieving functional impact scores for genes ...")

	projdb = ProjectDb(project["db"])

	data = ofm.retrieve_data(projdb)

	projdb.close()

	# save data matrix

	dst_path = os.path.join(project["temp_path"], "oncodrivefm-data.tdm")
	sgfi_path = os.path.join(project["temp_path"], "sample_gene-fimpact.tsv.gz")
	project["sample_gene_fi_data"] = sgfi_path

	log.info("Saving functional impact scores ...")
	log.debug("> {0}".format(dst_path))

	with open(dst_path, "w") as f:
		sgff = tsv.open(sgfi_path, "w")

		tsv.write_line(f, "SAMPLE", "GENE", "SIFT", "PPH2", "MA")
		tsv.write_line(sgff, "SAMPLE", "GENE",
					   "SIFT_SCORE", "SIFT_TFIC", "SIFT_TFIC_CLASS",
					   "PPH2_SCORE", "PPH2_TFIC", "PPH2_TFIC_CLASS",
					   "MA_SCORE", "MA_TFIC", "MA_TFIC_CLASS")

		for key, values in data.iteritems():
			sample, gene = key

			(sift_score, sift_tfic, sift_tfic_class,
				pph2_score, pph2_tfic, pph2_tfic_class,
				ma_score, ma_tfic, ma_tfic_class) = values

			tsv.write_line(f, sample, gene, sift_score, pph2_score, ma_score)
			tsv.write_line(sgff, sample, gene,
						   sift_score, sift_tfic, sift_tfic_class,
						   pph2_score, pph2_tfic, pph2_tfic_class,
						   ma_score, ma_tfic, ma_tfic_class, null_value="-")

		sgff.close()

	# count samples

	samples = set()
	gene_sample_count = defaultdict(int)
	for sample, gene in data.keys():
		samples.add(sample)
		gene_sample_count[gene] += 1

	num_samples = len(samples)

	if num_samples == 0:
		log.warn("There are no samples data, skipping OncodriveFM for this project")
		return

	ofm.load_config(num_samples)

	# Create a dataset with information on why some genes are not considered for calculation in OncodriveFM
	# There are basically two possible reasons:
	# - It does not pass the filter
	# - There are less samples mutated than the threshold

	exc_path = os.path.join(project["temp_path"], "oncodrivefm-excluded-cause.tsv")

	log.info("Saving excluded gene causes ...")
	log.debug("> {0}".format(exc_path))

	with tsv.open(exc_path, "w") as exf:
		tsv.write_line(exf, "GENE", "EXCLUDED_CAUSE")
		for gene, sample_count in gene_sample_count.items():
			causes = []
			if ofm.filter_enabled and not ofm.filter.valid(gene):
				causes += [ProjectDb.GENE_EXC_FILTER]
			if sample_count < ofm.genes_samples_threshold:
				causes += [ProjectDb.GENE_EXC_THRESHOLD]
			if len(causes) > 0:
				tsv.write_line(exf, gene, "".join(causes))

	base_conf = dict(
		data=dst_path,
		num_cores=config.oncodrivefm.num_cores,
		estimator=config.oncodrivefm.estimator,
		filter_enabled=ofm.filter_enabled,
		filter_path=ofm.filter_path)

	for slice_name in ["SIFT", "PPH2", "MA"]:
		projects_out_port.send(dict(project,
			oncodrivefm=dict(base_conf,
				 feature="genes",
				 slice=slice_name,
				 num_samplings=config.oncodrivefm.genes.num_samplings,
				 samples_threshold=ofm.genes_samples_threshold)))

	for slice_name in ["SIFT", "PPH2", "MA"]:
		projects_out_port.send(dict(project,
			oncodrivefm=dict(base_conf,
				 feature="pathways",
				 slice=slice_name,
				 num_samplings=config.oncodrivefm.pathways.num_samplings,
				 samples_threshold=ofm.pathways_samples_threshold)))

task.run()