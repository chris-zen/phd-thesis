import urllib
import urllib2

class BiomartService(object):
	def __init__(self, host = "biomart.org", port = 80, path = "/biomart/martservice"):
		if host.startswith("http"):
			raise Exception("The host is simply the host, not the url !")

		self.host = host
		self.port = port

		if not path.startswith("/"):
			path = "/" + path
		self.path = path.replace("/+", "/")

		self.url = "http://{}:{}{}".format(self.host, self.port, self.path)

	def query(self, query):
		data = urllib.urlencode({"query" : query})
		req = urllib2.Request(self.url, data)
		req.add_header("Content-Type", "text/xml")
		response = urllib2.urlopen(req)
		return response
