import os

from collections import defaultdict

from wok.task import task

from bgcore import tsv

from intogensm.config import GlobalConfig, PathsConfig
from intogensm.projects.db import ProjectDb
from intogensm.projects.results import ProjectResults
from intogensm.oncodriveclust import OncodriveClust, NON_SYN, SYN

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

	oclust = OncodriveClust(config.oncodriveclust, paths, log)

	project_results = ProjectResults(project)

	projdb = ProjectDb(project["db"])

	data = oclust.retrieve_data(projdb)

	projdb.close()

	data_paths = [
		os.path.join(project["temp_path"], "oncodriveclust-non-syn-data.tsv"),
		os.path.join(project["temp_path"], "oncodriveclust-syn-data.tsv")]

	log.info("Saving data ...")
	log.debug("> {0}".format(data_paths[NON_SYN]))
	log.debug("> {0}".format(data_paths[SYN]))

	df = [tsv.open(path, "w") for path in data_paths]

	gene_sample_count = defaultdict(int)

	for key, value in data.items():
		findex, gene, sample = key
		transcript, transcript_len, protein_pos = value

		if findex == NON_SYN:
			gene_sample_count[gene] += 1

			if oclust.filter_enabled and not oclust.filter.valid(gene):
				continue

		tsv.write_line(df[findex], gene, sample, protein_pos)

	for f in df:
		f.close()

	exc_path = os.path.join(project["temp_path"], "oncodriveclust-excluded-cause.tsv")

	log.info("Saving excluded gene causes ...")
	log.debug("> {0}".format(exc_path))

	with tsv.open(exc_path, "w") as exf:
		tsv.write_line(exf, "GENE", "EXCLUDED_CAUSE")
		for gene, sample_count in gene_sample_count.items():
			causes = []
			if oclust.filter_enabled and not oclust.filter.valid(gene):
				causes += [ProjectDb.GENE_EXC_FILTER]
			if sample_count < oclust.samples_threshold:
				causes += [ProjectDb.GENE_EXC_THRESHOLD]
			if len(causes) > 0:
				tsv.write_line(exf, gene, "".join(causes))

	log.info("Sending project ...")

	projects_out_port.send(dict(project,
								oncodriveclust=dict(
									data_paths=data_paths,
									samples_threshold=oclust.samples_threshold)))

task.run()