# -*- coding: utf-8 -*-

import httplib
import urllib

class ResponseReader(object):
	BUFFER_SIZE = 4 * 1024

	def __init__(self, response):
		self.response = response
		self.__last_buffer = None

	def __iter__(self):
		return self

	def read(self, *args, **kargs):
		return self.response.read(*args, **kargs)

	def __read_buffer(self):
		buffer = self.response.read(self.BUFFER_SIZE)
		if len(buffer) == 0:
			return None
		return buffer

	def readline(self):
		if self.__last_buffer is not None:
			buffer = self.__last_buffer
		else:
			buffer = self.__read_buffer()

		if buffer is None:
			return None

		line_buffer = []
		i = buffer.find("\n")
		while (i == -1 and buffer is not None):
			line_buffer.append(buffer)
			buffer = self.__read_buffer()
			if buffer is not None:
				i = buffer.find("\n")

		if buffer is not None:
			line_buffer.append(buffer[:i])
			self.__last_buffer = buffer[i + 1:]
			if len(self.__last_buffer) == 0:
				self.__last_buffer = None

		return "".join(line_buffer)

	def next(self):
		line = self.readline()
		if line is None:
			raise StopIteration
		return line

class RestClient(object):
	"""This is a very very simple restful client implementation"""

	def __init__(self, host, port = None, path = None):
		if port is None:
			port = 80
		elif isinstance(port, basestring):
			port = int(port)

		if path is None:
			path = "/"

		self.host = host
		self.port = port
		self.path = path
		
		self.conn = None
		self.__auto_connected = False

	def connect(self):
		self.close()
		self.conn = httplib.HTTPConnection("{0}:{1}".format(self.host, self.port))

	def close(self):
		if self.conn:
			self.conn.close()

	def compose_path(self, *parts):
		sb = []
		for part in parts:
			if part.startswith("/"):
				part = part[1:]
			sb += [part]
		return "/" + "/".join(sb)

	def request(self, method, resource, body = None, headers = {}):

		path = self.compose_path(self.path, resource)

		if body is not None and isinstance(body, dict):
			body = urllib.urlencode(body)
		
		self.conn.request(method, path, body, headers)

		response = self.conn.getresponse()
		if response.status not in [200, 202]:
			raise Exception("%s %s %s" % (response.status, response.reason, response.read()))
		print type(response.read())
		return ResponseReader(response)

	def post(self, resource, body = None, headers = {}):
		return self.request("POST", resource, body, headers)

	def get(self, resource, body = None, headers = {}):
		return self.request("GET", resource, body, headers)

	def _auto_connect(self):
		if not self.conn:
			self.__auto_connected = True
			self.connect()
		else:
			self.__auto_connected = False

	def _auto_close(self):
		if self.__auto_connected:
			self.__auto_connected = False
			self.close()

	def __repr__(self):
		sb = [self.host]
		if self.port != 80:
			sb += [":", str(self.port)]
		sb += [self.path]
		return "".join(sb)