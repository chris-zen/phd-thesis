from wok.config import Data, Config, BoolParam, IntParam, StringParam, ListParam, DataParam

class OncodriveFmGenesConfig(Config):
	num_samplings = IntParam(10000)
	threshold = StringParam("1%")

class OncodriveFmPathwaysConfig(Config):
	num_samplings = IntParam(10000)
	threshold = IntParam(10)

class OncodriveFmConfig(Config):
	genes = OncodriveFmGenesConfig()
	pathways = OncodriveFmPathwaysConfig()
	estimator = StringParam("mean")
	num_cores = IntParam(1)
	filter_enabled = BoolParam(True)
	filter_path = StringParam()

class OncodriveClustConfig(Config):
	samples_threshold = IntParam(5)
	filter_enabled = BoolParam(True)
	filter_path = StringParam()

class CombinationConfig(Config):
	classifiers = ListParam(Data.element)

class ProjectConfig(Config):
	annotations = DataParam()

class ResultsConfig(Config):
	purge_on_start = BoolParam(True)
	use_storage = BoolParam(True)
	purge_after_upload = BoolParam(True)
	create_zip = BoolParam(True)

class WebsiteConfig(Config):
	templates_path = StringParam()
	projects_list = StringParam()
	user_id = StringParam()

class GlobalConfig(Config):

	user_id = StringParam(required=True)
	workspace = StringParam(required=True)

	data_path = StringParam(required=True)
	results_path = StringParam(required=True)

	perl_bin = StringParam(required=True)
	perl_lib = StringParam(required=True)
	ext_bin_path = StringParam(required=True)

	ma_cache_path = StringParam(required=True)

	vardb_path = StringParam(required=True)
	sigdb_path = StringParam(required=True)

	local_temp_path = StringParam()
	local_temp_remove = BoolParam(True)
	shared_temp_remove = BoolParam(True)

	vep_partition_size = IntParam(100)
	consequences_overwrite = BoolParam(True)

	variants_only = BoolParam(False)
	skip_recurrences = BoolParam(False)
	skip_oncodrivefm = BoolParam(False)
	skip_oncodriveclust = BoolParam(False)

	oncodrivefm = OncodriveFmConfig()
	oncodriveclust = OncodriveClustConfig()

	combination = CombinationConfig()

	project = ProjectConfig()

	website = WebsiteConfig()

	results = ResultsConfig()

