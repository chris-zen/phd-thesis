import time
from datetime import timedelta

SUFFIXES = ['K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']

def hsize(size):
	if size < 0:
		raise ValueError('number must be non-negative')

	decimals = 0
	multiple = 1000.0
	for suffix in SUFFIXES:
		size /= multiple
		if size < multiple:
			fmt = "{0:." + str(3) + "f} {1}"
			return fmt.format(size, suffix)
		decimals += 3

	raise ValueError('number too large')

class RatedProgress(object):
	def __init__(self, logger, name="elements", interval=10.0):
		self.logger = logger
		self.name = name
		self.interval = 10.0

		self.start()

	def start(self):
		self.total_count = self.partial_count = 0

		self.total_start_time = self.partial_start_time = time.time()

	def update(self, count=1):
		self.total_count += count
		self.partial_count += count

		total_elapsed_time = time.time() - self.total_start_time
		partial_elapsed_time = time.time() - self.partial_start_time

		if partial_elapsed_time >= self.interval:
			total_ratio = float(self.total_count) / total_elapsed_time
			partial_ratio = float(self.partial_count) / partial_elapsed_time
			self.logger.debug("  {3} {0}, {1:.1f} [{2:.1f}] {0}/second".format(
				self.name, partial_ratio, total_ratio, hsize(self.total_count)))

			self.partial_count = 0
			self.partial_start_time = time.time()

	def log_totals(self):
		self.logger.info("  >> {1} {0}, {2:.1f} {0}/second".format(
			self.name, hsize(self.total_count), self.total_count / float(time.time() - self.total_start_time)))

	@property
	def elapsed_time(self):
		return timedelta(seconds=time.time() - self.total_start_time)