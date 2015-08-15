import os
import subprocess

from wok.task import task

from intogensm.config import GlobalConfig, PathsConfig

@task.foreach()
def oncoclust(project):
	log = task.logger

	config = GlobalConfig(task.conf)
	paths = PathsConfig(config)

	projects_out_port = task.ports("projects_out")

	project_id = project["id"]
	log.info("--- [{0}] --------------------------------------------".format(project_id))

	gene_transcripts_path = paths.data_ensembl_gene_transcripts_path()

	oclust = project["oncodriveclust"]

	data_paths = oclust["data_paths"]

	samples_threshold = oclust["samples_threshold"]

	oclust["results"] = os.path.join(project["temp_path"], "oncodriveclust-results.tsv")

	cmd = " ".join([
		"oncodriveclust",
		"-c",
		"-m", str(samples_threshold),
		"-o", oclust["results"],
		data_paths[0],
		data_paths[1],
		gene_transcripts_path
	])

	log.debug(cmd)

	ret_code = subprocess.call(cmd, shell=True)
	if ret_code == 1:
		log.warn("No results were generated")
	elif ret_code != 0:
		log.error("Error while executing OncodriveCLUST:\n{0}".format(cmd))

	projects_out_port.send(project)

task.run()