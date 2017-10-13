from queue import Queue

class LoggedQueue(Queue):
	logged = False
	def put(s, x):
		if s.logged:
			log(pp(x))
		super().put(x)
