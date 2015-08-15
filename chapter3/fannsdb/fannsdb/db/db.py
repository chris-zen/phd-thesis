class FannsDb(object):
	SOURCE_PREDICTOR_TYPE = "source"
	CALCULATED_PREDICTOR_TYPE = "calculated"

	TRANSCRIPT_MAP_TYPE = "transcript"
	PROTEIN_MAP_TYPE = "protein"

	def open(self, create=False):
		raise NotImplemented()

	def create(self):
		raise NotImplemented()

	def create_indices(self):
		raise NotImplemented()

	def drop_indices(self):
		raise NotImplemented()

	def commit(self):
		raise NotImplemented()

	def rollback(self):
		raise NotImplemented()

	def close(self):
		raise NotImplemented()

	def is_initialized(self):
		raise NotImplemented()

	def set_initialized(self, init=True):
		raise NotImplemented()

	def add_predictor(self, id, type, source=None):
		raise NotImplemented()

	def predictors(self, id=None, type=None):
		raise NotImplemented()

	def update_predictors(self, predictors=None):
		raise NotImplemented()

	def add_map(self, id, name, type, priority=0):
		raise NotImplemented()

	def add_map_item(self, id, source, value):
		raise NotImplemented()

	def remove_map(self, id):
		raise NotImplemented()

	def maps(self, id=None, type=None):
		raise NotImplemented()

	# for backward compatibility
	def query_transcripts(self, *args, **kwargs):
		self.query_scores(*args, **kwargs)

	def query_scores(self, fields=None, predictors=None, annotations=None, **filters):
		raise NotImplemented()

	def update_scores(self, docid, scores):
		raise NotImplemented()
