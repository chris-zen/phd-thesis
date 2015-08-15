import os

from bgcore.labelfilter import LabelFilter

from intogensm import so
from intogensm.config import GlobalConfig, PathsConfig
from intogensm.projects.db import ProjectDb

class OncodriveFm(object):
	"OncodriveFM helper"

	def __init__(self, config, paths, logger=None):
		"""
		:param config: intogensm.config.OncodriveFmConfig
		:param paths: PathsConfig
		:param logger: Optional logger
		"""

		self.config = config
		self.paths = paths
		self.logger = logger or get_logger("oncodrivefm")

		self.genes_samples_threshold = self.pathways_samples_threshold = None
		self.filter_enabled = self.filter_path = self.filter = None

	def load_expression_filter(self):
		default_filter = self.paths.data_gene_filter_path()
		self.filter_enabled = self.config.filter_enabled

		self.filter_path = self.config.filter_path or default_filter
		if self.filter_path is None: # user can assign a null
			self.filter_enabled = False
			self.filter_path = default_filter

		self.filter = LabelFilter()

		if self.filter_enabled:
			self.logger.info("Loading expression filter ...")
			self.logger.debug("> {0}".format(self.filter_path))
			self.filter.load(self.filter_path)

	def load_samples_thresholds(self, num_samples):
		self.genes_samples_threshold = get_threshold(self.logger, self.config.genes.threshold, num_samples)
		self.pathways_samples_threshold = get_threshold(self.logger, self.config.pathways.threshold, num_samples)

	def load_config(self, num_samples):
		self.load_expression_filter()
		self.load_samples_thresholds(num_samples)
		self.log_config()

	def log_config(self):
		self.logger.info("OncodriveFM configuration:")

		self.logger.info("  num_cores = {0}".format(self.config.num_cores))
		self.logger.info("  estimator = {0}".format(self.config.estimator))

		self.logger.info("  filter_enabled = {0}".format(self.filter_enabled))
		self.logger.info("  filter_path = {0}".format(
			os.path.basename(self.filter_path) if self.filter_path is not None else None))

		self.logger.info("  Genes:")

		self.logger.info("    num_samplings = {0}".format(self.config.genes.num_samplings))
		self.logger.info("    samples_threshold = {0}".format(self.genes_samples_threshold))

		self.logger.info("  Pathways:")

		self.logger.info("    num_samplings = {0}".format(self.config.pathways.num_samplings))
		self.logger.info("    samples_threshold = {0}".format(self.pathways_samples_threshold))

		return self

	_AGGREGATE = (max, max, min,
				  max, max, min,
				  max, max, min)

	def retrieve_data(self, projdb):
		data = {}

		self.logger.info("Retrieving gene alterations for OncodriveFM ...")

		for csq in projdb.consequences(join_samples=True, join_ctypes=False,
									   filters={ProjectDb.CSQ_CTYPES : so.ONCODRIVEFM}):

			var = csq.var
			for sample in var.samples:
				key = (sample.id, csq.gene)
				if key not in data:
					data[key] = (csq.sift_score, csq.sift_tfic, csq.sift_tfic_class,
								 csq.pph2_score, csq.pph2_tfic, csq.pph2_tfic_class,
								 csq.ma_score, csq.ma_tfic, csq.ma_tfic_class)
				else:
					a = data[key]

					b = (csq.sift_score, csq.sift_tfic, csq.sift_tfic_class,
						 csq.pph2_score, csq.pph2_tfic, csq.pph2_tfic_class,
						 csq.ma_score, csq.ma_tfic, csq.ma_tfic_class)

					c = [0.0] * len(a)

					for i in range(len(a)):
						c[i] = self._AGGREGATE[i](a[i], b[i])

					data[key] = tuple(c)

		return data


def get_threshold(log, threshold, num_samples):
	try:
		threshold = int(threshold)
	except:
		if not isinstance(threshold, basestring) or not threshold.endswith("%"):
			raise Exception("Wrong threshold value: {0}".format(threshold))

		threshold = threshold[0:-1]
		try:
			threshold = max(num_samples * int(threshold) / 100, 2)
		except:
			raise Exception("Wrong threshold value: {0}".format(threshold))

	return threshold
