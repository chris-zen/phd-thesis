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
def fimpact_run(partition):
	log = task.logger

	config = GlobalConfig(task.conf)
	paths = PathsConfig(config)

	results_port = task.ports("results")

	project = partition["project"]

	log.info("--- [{0} @ {1}] --------------------------------------------".format(project["id"], partition["index"]))

	log.info("Reading MA scores ...")

	ma_uniprot = {}
	ma_scores = {}

	with open(partition["ma_path"], "r") as f:
		for var_id, uniprot, fi_score in tsv.lines(f, (int, str, float), null_value="-"):
			ma_uniprot[var_id] = uniprot
			ma_scores[var_id] = fi_score

	log.info("Reading VEP results and calculating functional impact ...")

	tfic = TransFIC(data_path=paths.data_transfic_path())

	tfi_path = os.path.join(partition["base_path"], "{0:08d}.tfi".format(partition["index"]))
	cf = open(tfi_path, "w")

	with open(partition["vep_path"], "r") as f:
		for fields in tsv.lines(f, (int, str, str, str, str, str, str, float, float), null_value="-"):
			(var_id, gene, transcript, ct,
				protein_pos, aa_change, protein,
				sift_score, pph2_score) = fields

			ct = (ct or "").split(",")

			# Invert sift score
			if sift_score is not None:
				sift_score = 1.0 - sift_score

			ma_score = None

			uniprot = ma_uniprot.get(var_id)

			sift_impact = pph2_impact = ma_impact = None # TransFIC.UNKNOWN_IMPACT_CLASS

			coding_region = 1 if so.match(ct, so.CODING_REGION) else 0

			sift_tfic, sift_class, pph2_tfic, pph2_class, ma_tfic, ma_class = (None, None, None, None, None, None)

			ct_type = None
			if so.match(ct, so.NON_SYNONYMOUS):       # missense
				ct_type = TransFIC.CT_NON_SYNONYMOUS
				ma_score = ma_scores.get(var_id)

				(sift_tfic, sift_class,
				 pph2_tfic, pph2_class,
				 ma_tfic, ma_class) = tfic.calculate("gosmf", gene, ct_type, sift_score, pph2_score, ma_score)

				sift_impact = sift_class if sift_class in IMPACT_CLASSES else sift_impact
				pph2_impact = pph2_class if pph2_class in IMPACT_CLASSES else pph2_impact
				ma_impact = ma_class if ma_class in IMPACT_CLASSES else ma_impact
			elif so.match(ct, so.STOP):               # stop
				sift_impact = pph2_impact = ma_impact = TransFIC.HIGH_IMPACT_CLASS
				sift_score = pph2_score = 1.0
				ma_score = 3.5
			elif so.match(ct, so.FRAMESHIFT):         # frameshift
				sift_impact = pph2_impact = ma_impact = TransFIC.HIGH_IMPACT_CLASS
				sift_score = pph2_score = 1.0
				ma_score = 3.5
			elif so.match(ct, so.SPLICE_JUNCTION):    # splice junction
				sift_impact = pph2_impact = ma_impact = TransFIC.HIGH_IMPACT_CLASS
				sift_score = pph2_score = 1.0
				ma_score = 3.5
			elif so.match(ct, so.SPLICE_REGION):      # splice region
				sift_impact = pph2_impact = ma_impact = TransFIC.UNKNOWN_IMPACT_CLASS
				sift_score = pph2_score = 1.0
				ma_score = 3.5
			elif so.match(ct, so.SYNONYMOUS):         # synonymous
				sift_impact = pph2_impact = ma_impact = TransFIC.NONE_IMPACT_CLASS
				sift_score = pph2_score = 0.0
				ma_score = -2
			else:
				sift_impact = pph2_impact = ma_impact = TransFIC.NONE_IMPACT_CLASS

			aff_gene = (var_id, gene)

			# try to follow the convention http://www.hgvs.org/mutnomen/recs-prot.html
			prot_change = None
			if ct_type == TransFIC.CT_FRAMESHIFT:
				if protein_pos is None:
					prot_change = "fs"
				else:
					prot_change = "fs {0}".format(protein_pos)
				#log.debug("FRAMESHIFT: gene={}, protein={}, pos={}, change={}".format(gene, protein, protein_pos, aa_change))
			elif ct_type == "splice":
				prot_change = "r.spl?"
				#log.debug("SPLICE: gene={}, protein={}, pos={}, change={}".format(gene, protein, protein_pos, aa_change))
			elif protein_pos is not None and aa_change is not None:
				rc = ReContext()
				if rc.match(SIMPLE_AA_CHANGE_RE, aa_change):
					prot_change = "{ref}{pos}{alt}".format(pos=protein_pos, ref=rc.group(1), alt=rc.group(2) or "=")
				elif rc.match(COMPLEX_AA_CHANGE_RE, aa_change):
					prot_change = "{0} {1}".format(aa_change, protein_pos)
				else:
					log.warn("Unmatched aa change: gene={}, protein={}, pos={}, change={}, ct=[{}]".format(
													gene, protein, protein_pos, aa_change, ", ".join(ct)))

			tr_impact = ma_impact or pph2_impact or sift_impact or TransFIC.UNKNOWN_IMPACT_CLASS

			tsv.write_line(cf, var_id, transcript, gene, uniprot, prot_change, coding_region, tr_impact,
						   sift_score, sift_tfic, sift_class, sift_impact,
						   pph2_score, pph2_tfic, pph2_class, pph2_impact,
						   ma_score, ma_tfic, ma_class, ma_impact,
						   null_value="-")

	cf.close()

	# Send results to the next module
	partition["tfi_path"] = tfi_path
	results_port.send(partition)

task.run()