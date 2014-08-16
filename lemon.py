#!/usr/bin/python
# -*- coding: utf-8 -*-

version=0.2

try:
	import objgraph, gc
except:
	pass

import argparse, sys, os
import pickle, copy

import logger
from logger import log, topic
import frames
import project
import lemon_colors as colors
from keys import *

fast_forward = False # quickly replaying input events without drawing
sidebar = None # active sidebar
is_first_event = True # to know when to clear replay

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--eightbit', action='store_true',
				   help='try to be compatible with 8 bit color mode.')
	parser.add_argument('--dontblink', action='store_true',
				   help='dont blink the cursor.')
	parser.add_argument('--log-events', action='store_true',
				   help='what it says.')
	parser.add_argument('--noalpha', action='store_true',
				   help='avoid alpha blending')
	parser.add_argument('--mono', action='store_true',
				   help='no colors, just black and white')
	parser.add_argument('--webos', action='store_true',
				   help='webos keys hack')
	parser.add_argument('--invert', action='store_true',
				   help='invert colors')
	parser.add_argument('--font_size', action='store_true',
				   default=22)
	parser.add_argument('--replay', action='store_true',
				   default=False)
	return parser.parse_args()

args = parse_args()
colors.cache(args)


def cycle_sidebar():
	global sidebar
	sidebar = sidebars[sidebars.index(sidebar) + 1]

def top_keypress(event):
	k = event.key
	if k == K_ESCAPE:
		bye()
	elif k == K_F1:
		cycle_sidebar()
	else:
		return False
	return True



class KeypressEvent(object):
	def __init__(self, e):
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
			(pygame.key.name(self.key), self.uni, bin(self.mod)))

class MousedownEvent(object):
	def __init__(s, e):
		s.pos = pos
		s.button = button
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

				except EOFError:
					break

			fast_forward = False

	except IOError as e:
		log("couldnt open replay.p",e)


def keypress(e):
	reset_cursor_blink_timer()
	if args.log_events:
		log(e)

	if top_keypress(e):
		if args.log_events:
			log("handled by main top")
	elif sidebar.on_keypress(e):
		if args.log_events:
			log("handled by menu")
	else:
		root.on_keypress(e)

	render()

	"""
	try:
		gc.collect()
		objgraph.show_most_common_types(30)
	except:
		pass
	"""


def mousedown(e):
	reset_cursor_blink_timer()
	#handle ctrl + mousewheel font changing
	if e.button in [4,5] and (
		pygame.key.get_pressed()[pygame.K_LCTRL] or
		pygame.key.get_pressed()[pygame.K_RCTRL]):
		if e.button == 4: change_font_size(1)
		if e.button == 5: change_font_size(-1)
		render()
	else:
		for f in [logframe, sidebar, root]:
			if f.rect.collidepoint(e.pos):
				pos = (e.pos[0] - f.rect.x, e.pos[1] - f.rect.y)
				f.mousedown(e, pos)
				render()
				break


def pickle_event(e):
	with open("replay.p", "ab") as f:
		try:
			pickle.dump(e, f)
		except pickle.PicklingError as error:
			print error, ", are you profiling?"


def handle1(event):
	if event.type == KEYDOWN:
		if event.key == K_F2:
			ff = event.mod & KMOD_SHIFT
			do_replay(ff)
		else:
			if event.key == K_ESCAPE:
				bye()
			else:
				handle2(event)

	if event.type == MOUSEBUTTONDOWN:
		handle2(event)

def handle2(e):
	global is_first_event
	
	if is_first_event:
		clear_replay()
	pickle_event(e)
	handle3(e)
	is_first_event = False

def clear_replay():
	f = open("replay.p", 'w')
	f.truncate()
	f.close()

def handle3(e):
	if e.type == MOUSEDOWN:
		mousedown(e)
	elif e.type == KEYPRESS:
		keypress(e)
	else:
		raise 666

def render():
	root.render()
	sidebar.render()
	logframe.render()

def start():
	root.render()
	try:
		root.cursor_c, root.cursor_r = project.find(root.root['program'].ch.statements.items[0], root.lines)
		root.cursor_c += 1
	except Exception as e:
		print e, ", cant set initial cursor position"
	if args.replay:
		do_replay(True)
	render()

def bye():
	log("deading")
	sys.exit()

frames.args = args
frames.log_events = args.log_events

root = frames.Root()
if args.noalpha:
	root.arrows_visible = False

sidebars = [frames.Intro(root),
            frames.GlobalKeys(root),
            frames.Menu(root),
            frames.NodeInfo(root)]
            #frames.ContextInfo(root)]#carry on...
sidebars.append(sidebars[0])
sidebar = sidebars[2]

logframe = frames.Log()
logger.gui = logframe

allframes = sidebars + [logframe, root]

