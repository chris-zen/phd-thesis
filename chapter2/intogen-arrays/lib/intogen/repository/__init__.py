import rpath

def compose_url(repo_name, *path):
	return "{0}:{1}".format(repo_name, rpath.absolute(rpath.join(*path)))

def decompose_url(url):
	pos = url.index(":")
	repo_name = url[0:pos]
	path = rpath.absolute(url[pos + 1:])
	return (repo_name, path)

class Repository(object):
	def __init__(self, name):
		self._name = name

	def name(self):
		return self._name

	def url(self, *path):
		return compose_url(self._name, *path)