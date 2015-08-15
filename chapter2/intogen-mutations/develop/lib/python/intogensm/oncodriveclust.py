import os

from bgcore import tsv
from bgcore.labelfilter import LabelFilter

from wok.logger import get_logger

from intogensm import so
from intogensm.config import GlobalConfig, PathsConfig
from intogensm.projects.db import ProjectDb

NON_SYN = 0
SYN = 1

class OncodriveClust(object):
	"OncodriveCLUST helper"

	def __init__(self, config, paths, logger=None):
		"""
		:param config: intogensm.config.OncodriveClustConfig
		:param paths: PathsConfig
		:param logger: Optional logger
		"""

		self.config = config
		self.paths = paths
		self.logger = logger or get_logger("oncodriveclust")

		self._load_config()

	def _load_config(self):
		self.logger.info("OncodriveCLUST configuration:")

		self.samples_threshold = self.config.samples_threshold

		default_filter = self.paths.data_gene_filter_path()
		self.filter_enabled = self.config.filter_enabled
		self.filter_path = self.config.filter_path or default_filter
		if self.filter_path is None: # user can assign a null
			self.filter_enabled = False
			self.filter_path = default_filter

		self.logger.info("  samples_threshold = {0}".format(self.samples_threshold))
		self.logger.info("  genes_filter_enabled = {0}".format(self.filter_enabled))
		self.logger.info("  genes_filter_path = {0}".format(os.path.basename(self.filter_path)))

		self.filter = LabelFilter()

		if self.filter_enabled:
			self.logger.info("Loading expression filter ...")
			self.logger.debug("> {0}".format(self.filter_path))
			self.filter.load(self.filter_path)

		return self

	def load_cds_len(self, path):

		self.logger.info("Loading transcripts CDS length ...")
		self.logger.debug("> {}".format(path))

		cds_len = {}
		with tsv.open(path, "r") as f:
			for gene, transcript, transcript_len in tsv.lines(f, (str, str, int), header=True):
				cds_len[transcript] = transcript_len
		return cds_len

	def retrieve_data(self, projdb):

		cds_len = self.load_cds_len(self.paths.data_ensembl_gene_transcripts_path())
		data = {}

		self.logger.info("Retrieving gene alterations for OncodriveCLUST ...")

		for csq in projdb.consequences(join_samples=True,
									   filters={ProjectDb.CSQ_CTYPES : so.ONCODRIVECLUST | so.SYNONYMOUS}):

			if csq.transcript not in cds_len:
				continue

			transcript_len = cds_len[csq.transcript]

			if so.match(csq.ctypes, so.ONCODRIVECLUST):
				cls = NON_SYN
			elif so.match(csq.ctypes, so.SYNONYMOUS):
				cls = SYN
			else:
				continue

			for sample in csq.var.samples:
				key = (cls, csq.gene, sample.name)
				if key not in data:
					data[key] = (csq.transcript, transcript_len, csq.protein_pos)
				else:
					transcript, tlen, protein_pos = data[key]
					if transcript_len > tlen:
						data[key] = (csq.transcript, transcript_len, csq.protein_pos)

		return data