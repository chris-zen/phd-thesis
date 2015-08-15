import os

from wok.task import task

from bgcore import tsv

from intogensm.vep.local import VepLocal
from intogensm.vep.service import VepService
from intogensm.config import GlobalConfig, PathsConfig

@task.foreach()
def vep_run(partition):
	log = task.logger

	config = GlobalConfig(task.conf)

	results_port = task.ports("results")

	project_id = partition["project"]["id"]
	log.info("--- [{0} @ {1}] --------------------------------------------".format(project_id, partition["index"]))

	offline = "yes" # TODO: remove online mode

	if offline == "yes":
		log.info("Running VEP in local mode.")

		vep = VepLocal(
				perl_path=config.perl_bin,
				lib_path=config.perl_lib,
				script_path=os.path.join(config.ext_bin_path, "variant_effect_predictor", "variant_effect_predictor.pl"),
				cache_path=os.path.join(config.data_path, "vep_cache"))
	else:
		log.info("Running VEP using web services.")

		vep = VepService(cache_path=os.path.join(task.conf["cache_path"], "vep.db"))

	results_path = os.path.join(partition["base_path"], "{0:08d}.vep_out".format(partition["index"]))

	if not os.path.exists(results_path) or config.consequences_overwrite:
		# Run VEP
		vep.run(partition["bed_path"])

		log.info("Saving results ...")
		log.debug("VEP results: {0}".format(vep.results_path))

		# Save results

		with open(results_path, "w") as f:
			for r in vep.results():
				tsv.write_line(f, r.var_id, r.gene, r.transcript,
								",".join(r.consequences),
								r.protein_pos, r.aa_change, r.protein,
								r.sift, r.polyphen, null_value="-")

	else:
		log.warn("Skipping VEP, results already exist.")
		log.debug("VEP results: {0}".format(results_path))

	vep.close()

	# Send results to the next module
	partition["vep_path"] = results_path
	results_port.send(partition)

task.run()