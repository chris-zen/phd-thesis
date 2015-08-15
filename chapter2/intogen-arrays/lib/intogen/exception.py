import sys
import logging
import traceback

class PartialError(Exception):
	"""Class used to notify an error from inside a function processing
	a single element from a bunch of elements in a port.
	It shouldn't be considered as a module error but as a data element error
	so the module execution continues in the next data element"""

	CRITICAL	= logging.CRITICAL
	ERROR		= logging.ERROR
	WARNING		= logging.WARNING
	INFO		= logging.INFO
	DEBUG		= logging.DEBUG
	NOTSET		= logging.NOTSET

	def __init__(self, msg = None, level = ERROR, exc = False):
		self.msg = msg
		self.level = level
		self.exc_info = None
		if exc:
			self.exc_info = sys.exc_info()

	def __str__(self):
		sb = []
		if self.msg is not None:
			sb.append(self.msg)

		if self.exc_info is not None:
			if len(sb) > 0:
				sb.append("\n")

			sb.append(traceback.format_exception(
				self.exc_info[0], self.exc_info[1], self.exc_info[2]))

		return "".join(sb)

	def log(self, logger):
		if self.msg is not None:
			logger.log(self.level, self.msg)

		if self.exc_info is not None:
			exc_msg = traceback.format_exception(
				self.exc_info[0], self.exc_info[1], self.exc_info[2])

			logger.log(logging.ERROR, exc_msg)