import httplib, urlparse, base64

from lxml import etree

_EXIST_NS = 'http://exist.sourceforge.net/NS/exist'

_EXTENDED_QUERY = '''
<query xmlns="http://exist.sourceforge.net/NS/exist"%s>
  <text><![CDATA[ %s ]]></text>
  <properties>
    <property name="indent" value="yes"/>
    <property name="pretty-print" value="yes"/>
  </properties>
</query>
'''

def _extended_query_text(qtext, start = None, size = None, params = None):
	if params is not None:
		for k, v in params.items():
			name = "%%{%s}" % k
			if isinstance(v, list):
				v = ["'%s'" % (str(x)) for x in v]
				v = ",".join(v)

			qtext = qtext.replace(name, "(%s)" % (str(v)))

	args = []
	if start is not None:
		args += ['start="%s"' % start]
	if size is not None:
		args += ['max="%s"' % size]
	else:
		args += ['max="-1"']

	args_attrib = ""
	if len(args) > 0:
		args_attrib += " "
	args_attrib += " ".join(args)

	return _EXTENDED_QUERY % (args_attrib, qtext)

def _compose_path(base_path, path):
	sb = [base_path]
	
	if path is not None:
		if len(path) == 0 or path[0] != "/":
			sb += ["/"]
		sb += [path]

	return "".join(sb)

class Database(object):	
	def __init__(self, url, path = "/exist/rest/db"):
		r = urlparse.urlparse(url)
		try:
		    auth, netloc = r.netloc.split('@', 1)
		except ValueError:
		    auth   = ''
		    netloc = uri.netloc

		self.netloc = netloc
		self.path = r.path

		auth_parts = auth.split(':', 1)
		if len(auth_parts) == 0:
			self.user, self.password = (None, None)
		elif len(auth_parts) == 1:
			self.user, self.password = (auth_parts[0], None)
		elif len(auth_parts) == 2:
			self.user, self.password = (auth_parts[0], auth_parts[1])

	def __compose_connection_url(self, host, port):
		sb = []
		if host is None:
			sb += ["localhost"]
		else:
			sb += [host]
		if port is not None:
			sb += [":", str(port)]

		return "".join(sb)

	def _authorization(self, headers):
		if self.user is None:
			return

		if self.password is not None:
			auth = self.user + ':' + self.password
		else:
			auth = self.user

		auth = base64.encodestring(auth).strip()
		headers["Authorization"] = "Basic %s" % auth

	def _post(self, path, content):
		conn = httplib.HTTPConnection(self.netloc)

		headers = {"Content-Type" : "text/xml"}

		self._authorization(headers)

		resource_path = _compose_path(self.path, path)

		conn.request("POST", resource_path, content, headers)

		response = conn.getresponse()

		if response.status not in [200, 202]:
			raise Exception("%s %s %s" % (response.status, response.reason, response.read()))

		return ResponseStream(conn, response)

	def collection(self, path):
		return Collection(self, path)

class ResponseStream(object):
	def __init__(self, conn, response):
		self.conn = conn
		self.response = response

	def read(self, size = None):
		if size is None:
			return self.response.read()
		else:
			return self.response.read(size)

	def close(self):
		self.conn.close()

class Collection(object):
	def __init__(self, db, path):
		self.db = db
		self.path = path

	def _post(self, content):
		return self.db._post(self.path, content)

	def collection(self, path):
		return Collection(self.db, _compose_path(self.path, path))

	def xquery(self, qtext):
		return XQuery(self, qtext)

class XQuery(object):
	def __init__(self, collection, qtext):
		self.collection = collection
		self.qtext = qtext

	def _check_exception(self, root):
		if root.tag == 'exception':
			try:
				msg = root.find('message').text
			except AttributeError:
				msg = etree.tounicode(root)

			raise Exception(msg)

	def results_xml(self, start = None, size = None, params = {}):
		query = _extended_query_text(self.qtext, start, size, params)
		#print query

		stream = self.collection._post(query)
		tree = etree.parse(stream)
		stream.close()

		root = tree.getroot()
		#print etree.tostring(root)

		self._check_exception(root)

		return root

	def results_text(self, start = None, size = None, params = {}):
		query = _extended_query_text(self.qtext, start, size, params)
		stream = self.collection._post(query)

		tree = etree.parse(stream)
		stream.close()

		root = tree.getroot()

		self._check_exception(root)

		value = root.find("{%s}value" % _EXIST_NS)
		if value is None:
			raise Exception("<exist:value> not found at %s" % etree.tostring(root))

		return value.text

