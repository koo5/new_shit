from queue import Queue
from pprint import pformat

class LoggedQueue(Queue):
	logger = None
	def put(s, x):
		if s.logger:
			s.logger.debug(pformat(x))
		super().put(x)
