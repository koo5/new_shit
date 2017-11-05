# -*- coding: utf-8 -*-

from threading import Thread

from lemon_utils.utils import batch

from element import _collect_tags



class Collector(Thread):
	def __init__(s, x, callback):
		super().__init__()
		s.x = x
		s.callback = callback

	def run(s):
		print("run")
		for b in batch(_collect_tags(s.x, s.x.tags())):
			print("calling back")
			s.callback.callback(list(b))
		s.callback.callback([-1])
