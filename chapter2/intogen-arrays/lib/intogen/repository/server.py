from intogen.repository import decompose_url
from intogen.repository.local import LocalRepository

class RepositoryServer(object):
	def __init__(self, conf):
		self.repos = conf

	def repository(self, name):
		if name not in self.repos:
			raise Exception("Repository not found in the configuration: %s" % name)

		return LocalRepository(name, self.repos[name])

	def from_url(self, url):
		repo_name, path = decompose_url(url)
		return (self.repository(repo_name), path)

	def close(self):
		pass
