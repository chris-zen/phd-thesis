import os
import subprocess

from wok.task import task
from wok.config.data import Data

from intogensm.config import GlobalConfig, PathsConfig

@task.foreach()
def compute(project):
	log = task.logger

	config = GlobalConfig(task.conf)
	paths = PathsConfig(config)

	projects_out_port = task.ports("projects_out")

	project_id = project["id"]
	log.info("--- [{0}] --------------------------------------------".format(project_id))

	ofm = Data.element(project["oncodrivefm"])

	feature = ofm["feature"]
	slice_name = ofm["slice"]
	estimator = ofm.get("estimator")
	num_cores = ofm.get("num_cores", dtype=str)
	num_samplings = ofm.get("num_samplings", dtype=str)
	samples_threshold = ofm.get("samples_threshold", dtype=str)
	filter_enabled = ofm.get("filter_enabled", dtype=bool)
	filter_path = ofm.get("filter_path", dtype=str)

	log.info("feature = {0}".format(feature))
	log.info("slice = {0}".format(slice_name))
	log.info("estimator = {0}".format(estimator))
	log.info("num_cores = {0}".format(num_cores))
	log.info("num_samplings = {0}".format(num_samplings))
	log.info("samples_threshold = {0}".format(samples_threshold))
	log.info("filter_enabled = {0}".format(filter_enabled))
	log.info("filter_path = {0}".format(os.path.basename(filter_path)))

	cmd = [
		"oncodrivefm-compute",
		"-o", project["temp_path"],
		"-n oncodrivefm-{0}".format(feature),
		"-N", num_samplings,
		"--threshold", samples_threshold,
		"-e {0}".format(estimator),
		"-j", num_cores,
		"--slices '{0}'".format(slice_name)]

	if filter_enabled:
		cmd += ["--filter", filter_path]

	if feature == "pathways":
		cmd += ["-m", paths.data_kegg_path("ensg_kegg.tsv")]

	cmd += [ofm["data"]]

	project["oncodrivefm"] = dict(
		feature=feature,
		slice=slice_name,
		results=os.path.join(project["temp_path"], "oncodrivefm-{0}-{1}.tsv".format(feature, slice_name)))

	cmd = " ".join(cmd)

	log.debug(cmd)

	ret_code = subprocess.call(cmd, shell=True)
	if ret_code != 0:
		raise Exception("OncodriveFM error while computing {0}:\n{1}".format(feature, cmd))

	projects_out_port.send(project)

task.run()