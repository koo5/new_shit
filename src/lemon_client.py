# -*- coding: utf-8 -*-

"""(sdl/curses)-agnostic frontend stuff"""

import sys

import rpcing_frames
from keys import *
from lemon_args import args
import replay

import logging
logger=logging.getLogger("root")
log=logger.debug


if args.debug_objgraph:
	import objgraph, gc


class Client():
	def __init__(s, thread_message_signal, send_thread_message):
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
			rpcing_frames.server.init(thread_message_signal, send_thread_message)

			s.editor = rpcing_frames.Editor()
			s.logframe = rpcing_frames.Log()
			s.menu = rpcing_frames.Menu(s.editor)

			s.sidebars = [
			            s.menu,
			            rpcing_frames.InfoFrame(rpcing_frames.server.node_info),
			            rpcing_frames.InfoFrame(rpcing_frames.server.node_debug)]

			s.allframes = s.sidebars + [s.logframe, s.editor]

			s.sidebars.append(s.sidebars[0])#add a sentinel for easy cycling:)
			s.sidebar = s.sidebars[0] # currently active sidebar
			s.after_sidebar_changed()

	def bye(s):
		log("deading pygame..")
		import pygame
		pygame.quit()
		log("exit")
		sys.exit()


	def after_start(s):
		if args.load:
			rpcing_frames.server.load(args.load)

		if args.run:
			rpcing_frames.server.load(args.run)
			s.editor.root['loaded program'].run()

		if not args.kbdbg:
			s.initially_position_cursor()


		if args.replay:
			replay.do_replay(False)



	def initially_position_cursor(s):
		s.editor.maybe_redraw()

		s._initially_position_cursor()
		try:

			pass
		except Exception as e:
			log(e.__repr__(), ", cant set initial cursor position")

	def _initially_position_cursor(s):
		# if args.lesh:
		#	something = root.root['lesh'].command_line
		# else:
		something = s.editor.counterpart.root['repl'].ch.statements.items[0]
		s.editor.move_cursor(something)

	def after_sidebar_changed(s):
		for i in s.sidebars:
			i.visible = i == s.sidebar


	def cycle_sidebar(s):
		s.sidebar = s.sidebars[1 + s.sidebars.index(s.sidebar)]
		s.after_sidebar_changed()
		log("sidebar:%s", s.sidebar)
		redraw(666)

	def visibleframes(s):
		return [s.sidebar, s.logframe, s.editor]
