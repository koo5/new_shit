#!/usr/bin/python
# -*- coding: utf-8 -*-

"""frontend-agnostic middle, with input event replay functionality for debugging"""

from __future__ import print_function
from __future__ import unicode_literals

import sys
import pickle

from lemon_utils.lemon_logging import log, topic
import frames
import project
import lemon_colors as colors
from keys import *
from lemon_args import args
import lemon_utils.lemon_logging
lemon_utils.lemon_logging.do_topics = args.debug


if args.debug_objgraph:
	import objgraph, gc

version = "0.3 silly socks"

fast_forward = False # quickly replaying input events without drawing
sidebar = None # active sidebar
is_first_event = True # debug replay is cleared if first event isnt an F2 keypress so we need to track if this is the first event after program start


def cycle_sidebar():
	global sidebar
	sidebar = sidebars[sidebars.index(sidebar) + 1]


class KeypressEvent(object):
	def __init__(self, all, uni, key, mod):
		self.uni = uni
		self.key = key
		self.mod = mod
		self.all = all
		self.type = KEYDOWN

		if args.webos:
			self.webos_hack()

	def webos_hack(self):
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
	colors.cache(args)
	root.render()

	try:
		#if args.lesh:
		#	something = root.root[('lesh')].command_line
		#else:
		something = root.root.some_program.ch.statements.items[1]

		root.cursor_c, root.cursor_r = project.find(something, root.lines)
		#root.cursor_c += 1
	except Exception as e:
		log (e.__repr__(), ", cant set initial cursor position")

	#import parser_test
	#parser_test.test(root.root[('some program')].ch.statements.items[0])



	if args.load:
		load(args.load)

	if args.run:
		load(args.run)
		root.root.loaded_program.run()

	if args.replay:
		do_replay(False)

def load(name):
	assert(isinstance(name, unicode))
	frames.nodes.b_lemon_load_file(root.root, name)
	root.render()
	try_move_cursor(root.root.loaded_program)


def try_move_cursor(n):
	l = project.find(n, root.lines)
	if l:
		root.cursor_c, root.cursor_r = l




root = frames.Root()
logframe = frames.Log()

sidebars = [frames.Intro(root),
            frames.GlobalKeys(root),
            frames.Menu(root),
            frames.NodeInfo(root)]
            #frames.ContextInfo(root)]#carry on...
sidebars.append(sidebars[0])#a sentinel for easy cycling:)

sidebar = sidebars[2] # currently active sidebar


allframes = sidebars + [logframe, root]

def bye():
	log("deading")
	sys.exit()
