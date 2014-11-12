#!/usr/bin/python
# -*- coding: utf-8 -*-

#frontend-agnostic middle, complicated by debug replay functionality

from __future__ import print_function
from __future__ import unicode_literals

version=0.21

"""
try:
	import objgraph, gc
except:
	pass
"""
import sys, os
import pickle, copy

import lemon_logger
from lemon_logger import log, topic
import frames
import project
import lemon_colors as colors
from keys import *

fast_forward = False # quickly replaying input events without drawing
sidebar = None # active sidebar
is_first_event = True # debug replay is cleared if first event isnt an F2 keypress


def cycle_sidebar():
	global sidebar
	sidebar = sidebars[sidebars.index(sidebar) + 1]

def top_keypress(event):
	k = event.key
	ctrl = KMOD_CTRL & event.mod

	if k == K_F1:
		cycle_sidebar()
	elif ctrl and event.uni == '=':
		change_font_size(1)
	elif ctrl and event.uni == '-':
		change_font_size(-1)

	else:
		return False
	return True


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


@topic ("replay")
def do_replay(ff):
	global fast_forward
	import time
	try:
		with open("replay.p", "rb") as f:
			log("replaying...")
			if ff:
				fast_forward = True #ok, not much of a speedup. todo:dirtiness
			while 1:
				try:
					e = pickle.load(f)
					log(str(e))
					if e.type == KEYDOWN:
						keypress(e)
					elif e.type == MOUSEBUTTONDOWN:
						mousedown(e)
					else:
						raise Exception("unexpected event type:", e)
					render()
					if not fast_forward:
						draw()

				except EOFError:
					break

			fast_forward = False

	except IOError as e:
		log("couldnt open replay.p",e)


def keypress(e):
	if args.log_events:
		log(e)

	if top_keypress(e):
		if args.log_events:
			log("handled by main top")
	elif sidebar.on_keypress(e):
		if args.log_events:
			log("handled by menu")
	elif root.on_keypress(e):
		if args.log_events:
			log("handled by root")
	else:
		if args.log_events:
			log("unhandled")
	#render()#?

	"""
	try:
		gc.collect()
		objgraph.show_most_common_types(30)
	except:
		pass
	"""

def handle(event):
	if event.type == KEYDOWN:
		if event.key == K_F2:
			ff = event.mod & KMOD_SHIFT
			do_replay(ff)
		else:
			if event.key == K_ESCAPE:
				bye()
			else:
				record_and_handle(event)

	if event.type == MOUSEBUTTONDOWN:
		record_and_handle(event)

def record_and_handle(e):
	global is_first_event
	
	if is_first_event:
		clear_replay()
	pickle_event(e)
	dispatch(e)
	is_first_event = False

def dispatch(e):
	if e.type == MOUSEDOWN:
		mousedown(e)
	elif e.type == KEYPRESS:
		keypress(e)
	else:
		raise Exception("ehh")

def clear_replay():
	f = open("replay.p", 'w')
	f.truncate()
	f.close()

def pickle_event(e):
	with open("replay.p", "ab") as f:
		try:
			pickle.dump(e, f)
		except pickle.PicklingError as error:
			print (error, ", are you profiling?")


def start():
#	global root, sidebars, logframe, allframes
	frames.args = args
	#nodes.args = args

	colors.cache(args)
	root.render()

	try:
		if args.lesh:
			something = root.root['lesh'].command_line
		else:
			something = root.root['some program'].ch.statements.items[1]

		root.cursor_c, root.cursor_r = project.find(something, root.lines)
		#root.cursor_c += 1
	except Exception as e:
		print (e.__repr__(), ", cant set initial cursor position")

	#import parser_test
	#parser_test.test(root.root['some program'].ch.statements.items[0])



	if args.load:
		load(args.load)

	if args.run:
		load(args.run)
		root.root['loaded program'].run()

	if args.replay:
		do_replay(False)

def load(name):
	assert(isinstance(name, unicode))
	frames.nodes.b_lemon_load_file(root.root, name)
	root.render()
	try_move_cursor(root.root['loaded program'])


def try_move_cursor(n):
	l = project.find(n, root.lines)
	if l:
		root.cursor_c, root.cursor_r = l

root = frames.Root()

sidebars = [frames.Intro(root),
            frames.GlobalKeys(root),
            frames.Menu(root),
            frames.NodeInfo(root)]
            #frames.ContextInfo(root)]#carry on...
sidebars.append(sidebars[0])#sentinel:)
sidebar = sidebars[2]

logframe = frames.Log()
lemon_logger.gui = logframe

allframes = sidebars + [logframe, root]

def bye():
	log("deading")
	sys.exit()
