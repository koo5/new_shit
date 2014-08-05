#!/usr/bin/python
# -*- coding: utf-8 -*-


try:
	import objgraph, gc
except:
	pass


import argparse, sys, os
import pickle, copy

os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
import pygame
from pygame import display, image

import logger
from logger import log
import frames
import project
import colors


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

def change_font_size(by = 0):
	args.font_size += by
	frames.font = pygame.font.SysFont('monospace', args.font_size)
	frames.font_width, frames.font_height = frames.font.size("X")

def resize(size):
	global screen_surface, screen_width, screen_height
	log("resize to "+str(size))
	screen_surface = pygame.display.set_mode(size, flags)
	screen_width, screen_height = screen_surface.get_size()
	resize_frames()

sidebar = None
def resize_frames():
	logframe.rect.height = 110
	logframe.rect.width = screen_width
	logframe.rect.topleft = (0, screen_height - logframe.rect.height)

	root.rect.topleft = (0,0)
	root.rect.width = screen_width / 3 * 2
	root.rect.height = screen_height - logframe.rect.height

	if sidebar != None:
		sidebar.rect.topleft = (root.rect.w, 0)
		sidebar.rect.width = screen_width - root.rect.width
		sidebar.rect.height = root.rect.height

def cycle_sidebar():
	global sidebar
	sidebar = sidebars[sidebars.index(sidebar) + 1]
	resize_frames()

def top_keypress(event):
	global cursor_r,cursor_c, small_help
	k = event.key

	if pygame.KMOD_CTRL & event.mod:
		if event.uni == '=':
			change_font_size(1)
		elif event.uni == '-':
			change_font_size(-1)
		else:
			return False
	else:
		if k == pygame.K_ESCAPE:
			bye()
		elif k == pygame.K_F1:
			cycle_sidebar()
		else:
			return False
	return True




class KeypressEvent(object):
	def __init__(self, e):
		self.uni = e.unicode
		self.key = e.key
		self.mod = e.mod
		self.all = pygame.key.get_pressed()

		if args.webos:
			self.webos_hack()

	def webos_hack(self):
		if self.mod == 0b100000000000000:
			if self.key == pygame.K_r:
				self.key = pygame.K_UP
			if self.key == pygame.K_c:
				self.key = pygame.K_DOWN
			if self.key == pygame.K_d:
				self.key = pygame.K_LEFT
			if self.key == pygame.K_g:
				self.key = pygame.K_RIGHT

	def __repr__(self):
		return ("KeypressEvent(key=%s, uni=%s, mod=%s)" %
			(pygame.key.name(self.key), self.uni, bin(self.mod)))



replay = [] #todo, dont pickle the whole array every time (slowdown). but preserving the ability to replay current session might be nice
# http://stackoverflow.com/questions/12761991/how-to-use-append-with-pickle-in-python

def do_replay(ff):
	global replay, fast_forward
	try:
		with open("replay.p", "rb") as f:
			replay = pickle.load(f)
	except:
		log("couldnt read replay.p")
		replay = []
	if ff:
		fast_forward = True #ok, not much of a speedup. todo:dirtiness
		display.set_caption("replaying...")
		log("replaying...")
	for i in replay:
		display.set_caption(display.get_caption()[0] + " " + i.uni)
		log(i.uni)
		handle_keypress(copy.deepcopy(i))
	fast_forward = False



def keypress(event):
	reset_cursor_blink_timer()
	e = KeypressEvent(event)
	if args.log_events:
		log(e)

	if e.key == pygame.K_F2:
		do_replay(e.mod & pygame.KMOD_SHIFT)
	else:
		if e.key == pygame.K_ESCAPE:
			bye()
		else:
			replay.append(e)
			with open("replay.p", "wb") as f:
				try:
					pickle.dump(replay, f)
				except pickle.PicklingError as error:
					print error, ", are you profiling?"
		handle_keypress(copy.deepcopy(e))

def handle_keypress(e):
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


def process_event(event):

	if event.type == pygame.USEREVENT:
		pass # woke up python to poll for SIGINT

	if event.type == pygame.USEREVENT + 1:
		root.cursor_blink_phase = not root.cursor_blink_phase
		draw()

	if event.type == pygame.QUIT:
		bye()

	if event.type == pygame.KEYDOWN:
		keypress(event)

	if event.type == pygame.MOUSEBUTTONDOWN:
		mousedown(event)

	if event.type == pygame.VIDEORESIZE:
		resize(event.size)
		render()

	if event.type == pygame.ACTIVEEVENT:
		if event.gain:
			reset_cursor_blink_timer()
		else:
			pygame.time.set_timer(pygame.USEREVENT + 1, 0)#disable
			root.cursor_blink_phase = False
		draw()



def reset_cursor_blink_timer():
	if not args.dontblink:
		pygame.time.set_timer(pygame.USEREVENT + 1, 800)
	root.cursor_blink_phase = True



def render():
	root.render()
	sidebar.render()
	logframe.render()
	draw()


def draw():
	if not fast_forward:
		screen_surface.blit(root.draw(),root.rect.topleft)
		screen_surface.blit(sidebar.draw(),sidebar.rect.topleft)
		screen_surface.blit(logframe.draw(),logframe.rect.topleft)
		pygame.display.flip()

def bye():
	log("deading")
	pygame.display.iconify()
	sys.exit()

def loop():
	process_event(pygame.event.wait())






pygame.display.init()
pygame.font.init()

flags = pygame.RESIZABLE|pygame.DOUBLEBUF
#screen_surface = None
display.set_caption('lemon operating language prototype v 0.1')
icon = image.load('icon32x32.png')
display.set_icon(icon)

change_font_size()

frames.args = args
frames.log_events = args.log_events

root = frames.Root()
if args.noalpha:
	root.arrows_visible = False

sidebars = [frames.Intro(root),
            frames.GlobalKeys(root),
            frames.Menu(root),
            frames.NodeInfo(root)]
            #frames.ContextInfo(root)]
sidebars.append(sidebars[0])
sidebar = sidebars[2]

logframe = frames.Log()
logger.gui = logframe

def fuck_sdl():
	"""SDL insists that you must give your new window some size
	(screen_surface = pygame.display.set_mode), it ignores the WM
	but if the WM takes over...it doesnt even realize it!
	so it thinks it has the original size
	so i try to get the actual window size and "resize" """
	w = pygame.display.get_wm_info()["wmwindow"]
	import subprocess
	x =  subprocess.check_output(["xwininfo", "-id", str(w)])
	y = x.splitlines()
	for l in y:
		s = l.split()
		if len(s) > 1:
			if s[0] == "Width:":
				w = int(s[1])
			if s[0] == "Height:":
				h = int(s[1])
	return w,h

resize((666,666))
try:
	resize(fuck_sdl())
except Exception as e:
	print e, "failed to work around stupid sdl, will continue thinking the window is 666x666, please do a manual resize"


#try to set SDL keyboard settings to system settings
try:
	s = os.popen('xset -q  | grep "repeat delay"').read().split()
	repeat_delay, repeat_rate = int(s[3]), int(s[6])
	pygame.key.set_repeat(repeat_delay, 1000/repeat_rate)
except Exception as e:
	print e, "cant fix sdl keyboard repeat delay/rate"



root.render()
try:
	root.cursor_c, root.cursor_r = project.find(root.root['program'].ch.statements.items[0], root.lines)
	root.cursor_c += 1
except Exception as e:
	print e, ", cant set initial cursor position"


fast_forward = False

if args.replay:
	do_replay(True)

render()


pygame.time.set_timer(pygame.USEREVENT, 333) #poll for SIGINT
reset_cursor_blink_timer()
def main():
	while True:
		try:
			loop()
	#	except KeyboardInterrupt() as e:
	#		pygame.display.iconify()
	#		raise e
		except:
			pygame.display.iconify()
			raise

if __name__ == "__main__":
	main()
