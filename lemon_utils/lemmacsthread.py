import threading
from lemon_utils.loggedqueue import LoggedQueue


class LemmacsThread(threading.Thread):
	def __init__(s):
		super().__init__()
		s.input = LoggedQueue()
		s.output = LoggedQueue()

	def send_to_main_thread(s, msg):
		s.output.put(msg)
		s.send_thread_message()
