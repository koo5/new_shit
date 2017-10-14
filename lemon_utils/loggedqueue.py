from queue import Queue

class LoggedQueue(Queue):
	logged = False
	def put(s, x):
		if s.logged:
			s.logger.debug(pp(x))
		super().put(x)
