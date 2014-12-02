#!/usr/bin/python
# -*- coding: utf-8 -*-

"""frontend-agnostic middle, with input event replay functionality for debugging"""

from __future__ import print_function
from __future__ import unicode_literals

import sys
import pickle

from lemon_utils.lemon_logger import log, topic
import rpcing_frames as frames
import lemon_colors as colors
from keys import *
from lemon_args import args
import lemon_utils.lemon_logger
lemon_utils.lemon_logger.do_topics = args.debug


if args.debug_objgraph:
	import objgraph, gc


sidebar = None # the frame that is currently displayed in the sidebar
is_first_event = True # debug replay is cleared if first event isnt an F2 keypress so we need to track if this is the first event after program start


#F1
def cycle_sidebar():
	global sidebar
	sidebar = sidebars[sidebars.index(sidebar) + 1]


class KeypressEvent(object):
	"""a frontend-agnostic keypress event"""
	def __init__(self, all, uni, key, mod, frontend):
		"""
		:param all:an array of keys states as provided by SDL_GetKeyState. used for funky sideways cursor moving
		:param uni:unicode value
		:param key:contant from keys.py
		:param mod:-||-
		:param frontend:constant from lemon_platform
		"""
		self.uni = uni
		self.key = key
		self.mod = mod
		self.all = all
		self.type = KEYDOWN
		self.frontend = frontend

		if args.webos:
			#a hack for my Pre3:
			if self.mod == 0b100000000000000:
				if self.key == K_r:
					self.key = K_UP
				if self.key == K_c:
					self.key = K_DOWN
				if self.key == K_d:
					self.key = K_LEFT
				if self.key == K_g:
					self.key = K_RIGHT

	def __repr__(self):
		return ("KeypressEvent(key=%s, uni=%s, mod=%s)" %
			(self.key, self.uni, bin(self.mod)))


class MousedownEvent(object):
	def __init__(s, e):
		s.pos = e.pos
		s.button = e.button
		s.type = e.type


def start():
	server.after_start()

	colors.cache(args)

	if args.replay:
		do_replay(False)





editor = frames.Editor()
logframe = frames.Log()

sidebars = [#frames.Intro(root),
            #frames.GlobalKeys(root),
            frames.Menu(editor)]#,
            #frames.NodeInfo(root)]
            #frames.ContextInfo(root)]#carry on...
sidebars.append(sidebars[0])#a sentinel for easy cycling:)

sidebar = sidebars[0] # currently active sidebar


allframes = sidebars + [logframe, editor]


def bye():
	log("deading")
	sys.exit()
