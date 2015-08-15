from intogen.repository import rpath as rp
import os.path
import os

from intogen.repository import Repository

from intogen.io import FileReader, FileWriter

class LocalRepository(Repository):
	def __init__(self, name, base_path):
		Repository.__init__(self, name)
		
		self.base_path = os.path.abspath(base_path)

		#from wok import logger
		#self.log = logger.get_logger(None, name="repo")
		#self.log.info("Repository %s created with base path %s" % (name, base_path))

	def __local_path(self, path):
		path = rp.clean(path, absolute=True)[1:]
		path = os.path.join(self.base_path, path)
		path = os.path.normpath(path)
		relpath = os.path.relpath(path, self.base_path)
		if relpath.startswith(".."):
			raise Exception("Path going outside the base path: {0}".format(relpath))
		return path

	def exists(self, path):
		return os.path.exists(self.__local_path(path))

	def walk(self, path):
		raise Exception("Unimplemented method")

	def open_reader(self, path):
		return FileReader(self.__local_path(path))

	def open_writer(self, path):
		return FileWriter(self.__local_path(path))

	def mkdir(self, path, recursive = True):
		lpath = self.__local_path(path)
		if recursive:
			os.makedirs(lpath)
		else:
			os.mkdir(lpath)

	def mkdir_if_not_exists(self, path):
		lpath = self.__local_path(path)
		if not os.path.exists(lpath):
			try:
				os.makedirs(lpath)
			except:
				if not os.path.exists(lpath):
					raise

	def create_file(self, path):
		lpath = self.__local_path(path)
		f = open(lpath, "w")
		f.close()

	def create_local(self, path):
		lpath = self.__local_path(path)
		f = open(lpath, "w")
		f.close()
		return lpath

	def get_local(self, path):
		return self.__local_path(path)

	def close_local(self, local_path):
		pass

	def put_local(self, local_path):
		pass

	def close(self):
		pass
