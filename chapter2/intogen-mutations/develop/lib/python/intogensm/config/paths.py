import os

class PathsConfig(object):
	def __init__(self, config):
		self.config = config

	def results_path(self, *path):
		return os.path.join(self.config.results_path, self.config.user_id, self.config.workspace, *path)

	# Project ---------------------------------------------------------------------

	def projects_path(self, *path):
		return self.results_path("projects", *path)

	def project_path(self, project_id):
		return self.projects_path(project_id)

	def project_website_path(self, project_path, *path):
		return os.path.join(project_path, "website", *path)

	def project_results_path(self, project_path, *path):
		return os.path.join(project_path, "results", *path)

	def project_temp_path(self, project_path, *path):
		return os.path.join(project_path, "temp", *path)

	def project_quality_control_path(self, project_path, *path):
		return os.path.join(project_path, "quality_control", *path)

	# Combination paths ------------------------------------------------------------

	def combination_path(self, *path):
		return self.results_path("combination", *path)

	def create_combination_folders(self):
		combination_path = self.combination_path()
		if not os.path.exists(combination_path):
			os.makedirs(combination_path)
		for name in ["recurrences", "oncodrivefm", "oncodriveclust"]:
			path = os.path.join(combination_path, name)
			if not os.path.exists(path):
				os.makedirs(path)
		return combination_path

	# Data paths -------------------------------------------------------------------

	def data_path(self, *path):
		return os.path.join(self.config.data_path, *path)

	def data_transfic_path(self, *path):
		return self.data_path("TransFIC", *path)

	def data_ensembl_path(self, *path):
		return self.data_path("Ensembl", *path)

	def data_ensembl_genes_path(self):
		return self.data_ensembl_path("genes.tsv")

	def data_ensembl_gene_transcripts_path(self):
		return self.data_ensembl_path("gene_transcripts.tsv")

	def data_kegg_path(self, *path):
		return self.data_path("KEGG", *path)

	def data_kegg_def_path(self):
		return self.data_kegg_path("kegg.tsv")

	def data_kegg_ensg_map_path(self):
		return self.data_kegg_path("ensg_kegg.tsv")

	def data_gene_filter_path(self):
		return self.data_path("gene-filter.txt")

	# Examples -----------------------------------------------------------------------

	def examples_path(self, *path):
		return os.path.join(self.config.examples_path, *path)

#######################################################################################
### DEPRECATED
#######################################################################################

def get_results_path(conf, *path):
	return os.path.join(conf["results_path"], conf["user_id"], conf["workspace"], *path)

# Project ---------------------------------------------------------------------

def get_projects_path(conf, *path):
	return get_results_path(conf, "projects", *path)

def get_project_path(conf, project_id):
	return get_projects_path(conf, project_id)

def get_website_path(project_path, *path):
	return os.path.join(project_path, "website", *path)

def get_project_results_path(project_path, *path):
	return os.path.join(project_path, "results", *path)

def get_quality_control_path(project_path, *path):
	return os.path.join(project_path, "quality_control", *path)

# quality control (deprecated?) ----------------------------------------------------------------

def get_quality_variants_path(project_path):
	return os.path.join(project_path, "quality_variants.json")

def get_quality_oncodrivefm_path(project_path):
	return os.path.join(project_path, "quality_oncodrivefm.json")

def get_quality_oncodriveclust_path(project_path):
	return os.path.join(project_path, "quality_oncodriveclust.json")

# Temp (deprecated ?) -------------------------------------------------------------------------

def get_temp_path(conf, project_id=None):
	path = [conf["temp_path"], conf["user_id"], conf["workspace"]]
	if project_id is not None:
		path += [project_id]
	return os.path.join(*path)

# Combination paths ------------------------------------------------------------

def get_combination_path(conf, *path):
	return get_results_path(conf, "combination", *path)

def create_combination_folders(conf):
	combination_path = get_combination_path(conf)
	if not os.path.exists(combination_path):
		os.makedirs(combination_path)
	for name in ["recurrences", "oncodrivefm", "oncodriveclust"]:
		path = os.path.join(combination_path, name)
		if not os.path.exists(path):
			os.makedirs(path)
	return combination_path

# Data paths -------------------------------------------------------------------

def get_data_path(conf, *path):
	return os.path.join(conf["data_path"], *path)

def get_data_ensembl_path(conf, *path):
	return get_data_path(conf, "Ensembl", *path)

def get_data_ensembl_genes_path(conf):
	return get_data_ensembl_path(conf, "genes.tsv")

def get_data_ensembl_gene_transcripts_path(conf):
	return get_data_ensembl_path(conf, "gene_transcripts.tsv")

def get_data_kegg_path(conf, *path):
	return get_data_path(conf, "KEGG", *path)

def get_data_kegg_def_path(conf):
	return get_data_kegg_path(conf, "kegg.tsv")

def get_data_kegg_ensg_map_path(conf):
	return get_data_kegg_path(conf, "ensg_kegg.tsv")

def get_data_gene_filter_path(conf):
	return get_data_path(conf, "gene-filter.txt")

# Examples -----------------------------------------------------------------------

def get_examples_path(conf, *path):
	return os.path.join(conf["examples_path"], *path)
