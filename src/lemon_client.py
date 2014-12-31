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
