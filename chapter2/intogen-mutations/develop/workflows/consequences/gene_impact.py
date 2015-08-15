import re
import os.path

from wok.task import task

from bgcore import tsv
from bgcore.re import ReContext

from intogensm.transfic import TransFIC
from intogensm.config import GlobalConfig, PathsConfig
from intogensm import so

SIMPLE_AA_CHANGE_RE = re.compile(r"^([\*A-Z])(?:/([\*A-Z]))?$", re.IGNORECASE)
COMPLEX_AA_CHANGE_RE = re.compile(r"^([\*\-A-Z]+)(?:/([\*\-A-Z]+))?$", re.IGNORECASE)

IMPACT_CLASSES = set([
	TransFIC.HIGH_IMPACT_CLASS,
	TransFIC.MEDIUM_IMPACT_CLASS,
	TransFIC.LOW_IMPACT_CLASS])

def update_attr(attrs, key, attr_name, value, update, new=lambda value: value):
	if value is not None:
		if key not in attrs:
			attrs[key] = {attr_name : new(value)}
		elif attr_name not in attrs[key]:
			attrs[key][attr_name] = new(value)
		else:
			prev_value = attrs[key][attr_name]
			attrs[key][attr_name] = update(prev_value, value)

@task.foreach()
def gene_impact(project):
	log = task.logger

	config = GlobalConfig(task.conf)
	paths = PathsConfig(config)

	projects_port = task.ports("projects")

	log.info("--- [{0}] --------------------------------------------".format(project["id"]))

	partitions = project["partitions"]

	log.info("Reading {} partitions ...".format(len(partitions)))

	aff_gene_attrs = {}

	for partition in partitions:
		log.info(" Partition {} ...".format(partition["index"]))
		with open(partition["tfi_path"], "r") as f:
			bool_type = lambda val: bool(int(val)) if val is not None else False
			types = (int, str, str, bool_type, int, int, int, int)
			columns = [0, 2, 4, 5, 6, 10, 14, 18]
			for fields in tsv.lines(f, types, columns=columns, null_value="-"):
				(var_id, gene, prot_change, coding_region, tr_impact,
				 	sift_impact, pph2_impact, ma_impact) = fields

				coding_region = coding_region == 1

				aff_gene = (var_id, gene)

				# update aggregated impact for all the predictors
				update_attr(aff_gene_attrs, aff_gene, "sift_impact", sift_impact, update=TransFIC.higher_impact)
				update_attr(aff_gene_attrs, aff_gene, "pph2_impact", pph2_impact, update=TransFIC.higher_impact)
				update_attr(aff_gene_attrs, aff_gene, "ma_impact", ma_impact, update=TransFIC.higher_impact)

				# update whether the affected gene is a coding region or not
				update_attr(aff_gene_attrs, aff_gene, "coding_region", coding_region,
							update=lambda prev_value, value: prev_value or value)

				# aggregate protein changes per affected_gene
				if prot_change is not None:
					update_attr(aff_gene_attrs, aff_gene, "prot_changes", prot_change,
									 new=lambda value: set([value]),
									 update=lambda prev_value, value: prev_value | set([value]))

	num_vars = len(set([var_id for var_id, gene in aff_gene_attrs.keys()]))
	num_genes = len(set([gene for var_id, gene in aff_gene_attrs.keys()]))
	log.info("Saving {} variant-gene impacts ({} variants and {} genes) ...".format(len(aff_gene_attrs), num_vars, num_genes))

	gfi_path = os.path.join(project["csq_path"], "variant-gene_impact.tsv")
	with open(gfi_path, "w") as vf:
		for aff_gene, attrs in aff_gene_attrs.items():
			var_id, gene = aff_gene

			# get the impact by trust priority: ma, pph2, sift
			impact = attrs.get("ma_impact") or attrs.get("pph2_impact") or attrs.get("sift_impact") or TransFIC.UNKNOWN_IMPACT_CLASS

			coding_region = attrs.get("coding_region", False)
			coding_region = 1 if coding_region else 0

			prot_changes = attrs.get("prot_changes")
			prot_changes = ",".join(prot_changes) if prot_changes is not None else None

			tsv.write_line(vf, var_id, gene, impact, coding_region, prot_changes, null_value="-")

	# Send results to the next module
	project["gfi_path"] = gfi_path
	projects_port.send(project)

task.run()