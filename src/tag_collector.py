# -*- coding: utf-8 -*-

from threading import Thread
from lemon_utils.utils import batch
from element import _collect_tags

class Collector(Thread):
	def __init__(s, x, callback, source):
		super().__init__()
		s.x = x
		s.callback = callback
		s.source = source

	def run(s):
		print("run")
		#import cProfile, pstats;pr = cProfile.Profile();pr.enable()
		#for b in batch(_collect_tags(s.x, s.x.tags())):
		import sys
		for b in s.source:
			#print(b)
			print("calling back")
			#s.callback.callback((b))
			s.callback.callback(list(b))
			pass
		#pr.disable();pstats.Stats(pr).sort_stats('cumtime').print_stats(20)
		s.callback.callback([-1])
		#from IPython import embed; embed()
