# -*- coding: utf-8 -*-

"""(sdl/curses)-agnostic frontend stuff"""

import sys

from lemon_utils.lemon_logging import log
import rpcing_frames
from keys import *
from lemon_args import args
import lemon_utils.lemon_logging
lemon_utils.lemon_logging.do_topics = args.debug


if args.debug_objgraph:
	import objgraph, gc


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

		self.mods = set([x for x in [KMOD_CTRL, KMOD_ALT] if mod & x])

	def __repr__(self):
		return ("KeypressEvent(key=%s, uni=%s, mod=%s)" %
			(self.key, self.uni, bin(self.mod)))


class MousedownEvent(object):
	def __init__(s, e):
		s.pos = e.pos
		s.button = e.button
		s.type = e.type


class Client():
	def __init__(s):
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

			s.editor = rpcing_frames.Editor()
			s.logframe = rpcing_frames.Log()
			s.menu = rpcing_frames.Menu(s.editor)

			s.sidebars = [#frames.Intro(root),
			            #frames.GlobalKeys(root),
			            s.menu]#,
			            #frames.NodeInfo(root)]
			            #frames.ContextInfo(root)]#carry on...

			s.allframes = s.sidebars + [s.logframe, s.editor]

			s.sidebars.append(s.sidebars[0])#add a sentinel for easy cycling:)
			s.sidebar = s.sidebars[0] # currently active sidebar

	def bye(s):
		log("deading pygame..")
		import pygame
		pygame.quit()
		log("exit")
		sys.exit()


	def after_start(s):
		if args.replay:
			do_replay(False)


	def cycle_sidebar(s):
		s.sidebar = s.sidebars[s.sidebars.index(s.sidebar) + 1]
		log("sidebar:%s", s.sidebar)

	def visibleframes(s):
		return [s.sidebar, s.logframe, s.editor]
