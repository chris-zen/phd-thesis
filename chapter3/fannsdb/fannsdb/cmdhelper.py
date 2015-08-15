import os
import errno

from bgcore import logging as bglogging
from fannsdb.db.sqlitedb import FannsSQLiteDb
from fannsdb.db.mongodb import FannsMongoDb


class Command(object):
	@classmethod
	def withtraits(cls, *args):
		return type(cls.__name__, args + (cls,), {})

	def __init__(self, parser):
		self._parser = parser
		self.args = None
		self.logger = None

	def parse_args(self, logger_name):
		bglogging.add_logging_arguments(self._parser)

		self.args = self._parser.parse_args()

		bglogging.initialize(self.args)

		self.logger = bglogging.get_logger(logger_name)

		return self.args, self.logger

	def handle_error(self, ex=None):
		if ex is None:
			import sys
			ex = sys.exc_info()[1]

		if isinstance(ex, KeyboardInterrupt):
			self.logger.warn("Interrupted by Ctrl-C")
		elif not isinstance(ex, IOError) or ex.errno != errno.EPIPE:
			self.logger.error(repr(ex))
			from traceback import format_exc
			self.logger.debug(format_exc())
		return -1

class DbTrait(object):

	DEFAULT_DB_NAME = "funcscores.db"

	def __init__(self, *args, **kwargs):
		super(DbTrait, self).__init__(*args, **kwargs)
		self.db = None

	def add_db_args(self):
		self._parser.add_argument("db_path", metavar="DB_PATH", help="Database path")

	def open_db(self):
		if self.args.db_path is None:
			self.args.db_path = self.DEFAULT_DB_NAME

		self.logger.info("Opening database {} ...".format(os.path.basename(self.args.db_path)))

		db = FannsSQLiteDb(self.args.db_path)
		db.open()

		if not db.is_initialized():
			self.logger.error("The database is not initialized")
			db.close()
			exit(-1)

		self.db = db
		return db

	def create_db(self):
		if self.args.db_path is None:
			self.args.db_path = self.DEFAULT_DB_NAME

		self.logger.info("Creating database ...")

		db = FannsSQLiteDb(self.args.db_path)
		db.open(create=True)

		if db.is_initialized():
			self.logger.error("The database already exists and it is initialized")
			db.close()
			exit(-1)

		self.db = db
		return db

	def handle_error(self, ex=None):
		super(DbTrait, self).handle_error(ex)
		if self.db is not None:
			self.db.rollback()

class MongoDbTrait(object):

	DEFAULT_URL = "mongodb://localhost/fannsdb"

	def __init__(self, *args, **kwargs):
		super(MongoDbTrait, self).__init__(*args, **kwargs)
		self.db = None

	def add_db_args(self):
		self._parser.add_argument("db_uri", metavar="DB_URI", help="Database URI")

	def open_db(self):
		if self.args.db_uri is None:
			self.args.db_uri = self.DEFAULT_URL

		self.logger.info("Opening database {} ...".format(self.args.db_uri))

		db = FannsMongoDb(uri=self.args.db_uri)
		db.open()

		if not db.is_initialized():
			self.logger.error("The database is not initialized")
			db.close()
			exit(-1)

		self.db = db
		return db

	def create_db(self):
		if self.args.db_url is None:
			self.args.db_url = self.DEFAULT_URL

		self.logger.info("Creating database ...")

		db = FannsMongoDb(self.args.db_url)
		db.open(create=True)

		if db.is_initialized():
			self.logger.error("The database already exists and it is initialized")
			db.close()
			exit(-1)

		self.db = db
		return db

	def handle_error(self, ex=None):
		super(MongoDbTrait, self).handle_error(ex)
		if self.db is not None:
			self.db.rollback()

class PredictorsTrait(object):
	def add_selected_predictors_args(self):
		self._parser.add_argument("-p", "--predictors", dest="predictors", metavar="PREDICTORS",
									help="Comma separated list of predictors")

	def get_selected_predictors(self, available_predictors=None, check_missing=True):
		if self.args.predictors is not None:
			predictors = [p.strip() for p in self.args.predictors.split(",")]
			available_predictors = set(available_predictors) if available_predictors is not None else None
			if available_predictors is not None and check_missing:
				missing_predictors = [p for p in predictors if p not in available_predictors]
				if len(missing_predictors) > 0:
					self.logger.error("Missing predictors: {}".format(", ".join(missing_predictors)))
					self.logger.error("Available predictors: {}".format(", ".join(available_predictors)))
					exit(-1)
			predictors = [p for p in predictors if available_predictors is None or p in available_predictors]
		else:
			predictors = available_predictors

		if predictors is not None:
			self.logger.info("Selected predictors: {}".format(", ".join(predictors)))

		return predictors

class PredictorsInDbTrait(object):

	def add_selected_predictors_args(self):
		self._parser.add_argument("-p", "--predictors", dest="predictors", metavar="PREDICTORS",
									help="Comma separated list of predictors. Use '*' for all available predictors.")

	def get_selected_predictors(self, db=None, default_all=False, check_missing=True):
		if db is None:
			db = self.db

		db_predictors = [pred["id"] for pred in db.predictors()]

		predictors = None

		if self.args.predictors is not None:
			if self.args.predictors == "*":
				predictors = db_predictors
			else:
				predictors = [p.strip() for p in self.args.predictors.split(",")]
				if check_missing:
					missing_predictors = [pid for pid in predictors if pid not in set(db_predictors)]
					if len(missing_predictors) > 0:
						self.logger.error("Predictors not found in the database: {}.".format(", ".join(missing_predictors)))
						self.logger.error("Available predictors: {}".format(", ".join(db_predictors)))
						exit(-1)

		elif default_all:
			predictors = db_predictors

		if predictors is not None and len(predictors) > 0:
			self.logger.info("Selected predictors: {}".format(", ".join(predictors)))

		return predictors or []

class AnnotationsTrait(object):

	def add_selected_annotations_args(self):
		self._parser.add_argument("-a", "--annotations", dest="annotations", metavar="ANNOTATIONS",
									help="Comma separated list of annotations. Use '*' for all available annotations.")

	def get_selected_annotations(self, db=None, default_all=False):
		if db is None:
			db = self.db

		db_annotations = [ann["id"] for ann in db.maps()]

		annotations = None

		if self.args.maps is not None:
			if self.args.maps == "*":
				annotations = [ann["id"] for ann in db.maps()]
			else:
				annotations = [a.strip() for a in self.args.maps.split(",")]
				missing_annotations = [aid for aid in annotations if aid not in set(db_annotations)]
				if len(missing_annotations) > 0:
					self.logger.error("Annotations not found in the database: {}".format(", ".join(missing_annotations)))
					self.logger.error("Available annotations: {}".format(", ".join(db_annotations)))
					exit(-1)

		elif default_all:
			annotations = [ann["id"] for ann in db.maps()]

		if annotations is not None and len(annotations) > 0:
			self.logger.info("Selected annotations: {}".format(", ".join(annotations)))

		return annotations or []

class ColumnsTrait(object):

	COORDINATE_COLUMNS = ["chr", "strand", "start", "ref", "alt", "transcript",
						  "aa_pos", "aa_ref", "aa_alt", "protein"]

	def add_selected_columns_args(self):
		self._parser.add_argument("-c", "--columns", dest="columns", metavar="COLUMNS",
									help="Comma separated list of coordinates columns. "
										 "Available columns: {}".format(self.COORDINATE_COLUMNS))

	def get_selected_columns(self, default_columns=None):
		default_columns = default_columns or self.COORDINATE_COLUMNS

		if self.args.columns is not None:
			columns = [col.lower() for col in self.args.columns.split(",")]
			missing_columns = [col for col in columns if col not in set(default_columns)]
			if len(missing_columns) > 0:
				self.logger.error("Columns not found in the database: {}".format(", ".join(missing_columns)))
				self.logger.error("Available columns: {}".format(", ".join(default_columns)))
				exit(-1)
			self.logger.info("Selected columns: {}".format(", ".join(columns)))
		else:
			columns = default_columns

		return columns

class TransformsTrait(object):
	def add_transform_args(self):
		self._parser.add_argument("-t", "--transform", dest="transforms", metavar="PREDICTOR=EXPR", action="append",
						help="Transform scores of PREDICTOR with a Python EXPRession. Example: SIFT=log(x/(1-x)).")

	def get_transforms(self, predictors=None):
		transforms = {}
		if self.args.transforms is not None:
			namespace = {}

			allowed_builtins = set(["abs", "divmod", "float", "int", "long", "max", "min", "pow", "round", "sum"])
			for name, f in __builtins__.items():
				if name in allowed_builtins:
					namespace[name] = f

			import math
			for name, f in vars(math).items():
				if not name.startswith("_"):
					namespace[name] = f

			for trs in self.args.transforms:
				pos = trs.find("=")
				if pos == -1:
					self.logger.error("Wrong transformation: {}".format(trs))
					exit(-1)
				predictor = trs[:pos]
				expr = trs[pos+1:]
				try:
					func = eval("lambda x: {}".format(expr), {"__builtins__" : namespace}, {})
				except:
					self.logger.error("Wrong expression for transformation: {}".format(trs))

				if predictor not in transforms:
					transforms[predictor] = [(expr, func)]
				else:
					transforms[predictor] += [(expr, func)]

		if len(transforms) > 0:
			self.logger.info("Predictors transformations:")
			for predictor in predictors or sorted(transforms.keys()):
				if predictor in transforms:
					self.logger.info("  {}:".format(predictor))
					for expr, _ in transforms[predictor]:
						self.logger.info("    {}".format(expr))

		return transforms

DefaultCommandHelper = Command.withtraits(MongoDbTrait, PredictorsInDbTrait, AnnotationsTrait, ColumnsTrait, TransformsTrait)
