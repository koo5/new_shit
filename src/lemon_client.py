#!/usr/bin/python
# -*- coding: utf-8 -*-

"""(sdl/curses)-agnostic frontend stuff,
with input event replay functionality for debugging"""

import sys

from lemon_utils.lemon_logging import log
import rpcing_frames
import lemon_colors as colors
from keys import *
from lemon_args import args
import lemon_utils.lemon_logging
lemon_utils.lemon_logging.do_topics = args.debug


if args.debug_objgraph:
	import objgraph, gc



sidebar = None # the frame that is currently displayed in the sidebar
is_first_event = True # debug replay is cleared if first event isnt an F2 keypress so we need to track if this is the first event after program start


#F1
def cycle_sidebar():
	global sidebar
	sidebar = sidebars[sidebars.index(sidebar) + 1]
	log("sidebar:%s", sidebar)

def visibleframes():
	return [sidebar, logframe, editor]

class KeypressEvent(object):
	"""a frontend-agnostic keypress event"""
	def __init__(self, all, uni, key, mod):
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
	#server.after_start()

	colors.cache(args)

	if args.replay:
		do_replay(False)

def bye():
	log("deading")
	sys.exit()


def setup():
	#if args.rpc:
	#	lemon_logger.debug_out = client_debug_out
	#else: logging goes thru the log frame
	pass

#if args.log:
#	frame = rpcing_frames.Log()
if args.rpc:
	"""select which frames we want to display"""
	raise Exception('not finished')
	if args.intro:
		frames = [rpcing_frames.StaticInfoFrame(server.intro)]
	elif args.editor:
		frames = [rpcing_frames.editor]
	else:
		raise Exception("rpc but no frame? try --root or --menu")

else:

	editor = rpcing_frames.Editor()
	logframe = rpcing_frames.Log()
	menu = rpcing_frames.Menu(editor)

	sidebars = [#frames.Intro(root),
	            #frames.GlobalKeys(root),
	            menu]#,
	            #frames.NodeInfo(root)]
	            #frames.ContextInfo(root)]#carry on...

	allframes = sidebars + [logframe, editor]

	sidebars.append(sidebars[0])#add a sentinel for easy cycling:)
	sidebar = sidebars[0] # currently active sidebar





