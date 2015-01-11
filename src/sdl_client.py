#!/usr/bin/python3
# -*- coding: utf-8 -*-


import os, sys
import subprocess
from math import *
from pprint import pformat as pp
from copy import copy


from pizco import Signal


from lemon_utils.lemon_six import iteritems
from lemon_utils.utils import Evil
from lemon_utils.lemon_logging import log, info


import lemon_args
lemon_args.parse_args()
from lemon_args import args
from frontend_events import *


os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
if False:#hasattr(sys, 'pypy_version_info'):
	print ("trying to load pygame_cffi, adding pygame_cffi to sys.path")
	try:
		sys.path.append("pygame_cffi")
		import pygame
		if hasattr(pygame, 'cffi'):
			print("yep, loaded pygame_cffi")
	except:
		sys.path.remove("pygame_cffi")
import pygame
from pygame import display, image, Rect, time
flags = pygame.RESIZABLE|pygame.DOUBLEBUF


display.init()
if args.freetype:
	from pygame import freetype
	freetype.init(cache_size=1024)
else:
	import pygame.font
	pygame.font.init()


import lemon_platform
lemon_platform.SDL = True


import lemon_client, rpcing_frames
import keybindings
import replay




def reset_cursor_blink_timer():
	if not args.dontblink:
		pygame.time.set_timer(pygame.USEREVENT + 1, 1600)
	c.editor.cursor_blink_phase = True

def user_change_font_size(by = 0):
	change_font_size(by)
	resize_frames()
	redraw(666)
keybindings.change_font_size = user_change_font_size


def change_font_size(by = 0):
	global font, font_width, font_height
	args.font_size += by
	if args.freetype:
		rpcing_frames.font = font = freetype.SysFont('monospace', args.font_size)
		font.origin = True
		_, _, font_width, _ = font.get_rect("X")
		font_height = font.get_sized_glyph_height()
		rpcing_frames.font_width, rpcing_frames.font_height = font_width, font_height
	else:
		rpcing_frames.font = font = pygame.font.SysFont('monospace', args.font_size)
		rpcing_frames.font_width, rpcing_frames.font_height = font_width, font_height = font.size("X")


def resize(size):
	global screen_surface, screen_width, screen_height
	log("resize to "+str(size))
	rpcing_frames.sdl_screen_surface = screen_surface = pygame.display.set_mode(size, flags)
	screen_width, screen_height = screen_surface.get_size()
	resize_frames()
	redraw(666)
replay.resize = resize

def resize_frames():
		c.logframe.rect = Rect (
			0, screen_height - args.log_height,
			screen_width, args.log_height * font_height)

		c.editor.rect = Rect(0,0,
			screen_width // 3 * 2,
			screen_height - args.log_height)

		sidebar_rect = Rect(c.editor.rect.w, 0,
		    screen_width - c.editor.rect.width,
			c.editor.rect.height)

		for frame in c.sidebars:
			frame.rect = sidebar_rect

		for f in c.allframes:
			f.cols = f.rect.width // font_width
			f.rows = f.rect.height // font_height
			log((f, f.cols, f.rows))

		log("resized frames")


def pygame_keypressevent__repr__(self):
		#a better repr that translates keys to key names
		return ("KeypressEvent(key=%s, uni=%s, mod=%s)" %
			(pygame.key.name(self.key), self.uni, bin(self.mod)))
KeypressEvent.__repr__ = pygame_keypressevent__repr__


def keypress(e):
	reset_cursor_blink_timer()
	keybindings.keypress(e)


def mousedown(e):
	reset_cursor_blink_timer()
	#handle ctrl + mousewheel font changing
	if e.button in [4,5] and (
		pygame.key.get_pressed()[pygame.K_LCTRL] or
		pygame.key.get_pressed()[pygame.K_RCTRL]):
			if e.button == 4: user_change_font_size(1)
			if e.button == 5: user_change_font_size(-1)
	else:
		for f in c.visibleframes():
			if f.rect.collidepoint(e.pos):
				e.pos = (e.pos[0] - f.rect.x, e.pos[1] - f.rect.y)
				f.sdl_mousedown(e)
				break


def dispatch_input_event(event):
	if type(event) == KeypressEvent:
		keypress(event)
		return True

	elif type(event) == MousedownEvent:
		mousedown(event)
		return True

	elif type(event) == ResizeEvent:
		resize(event.size)
		return True

	else:
		raise Exception("unexpected event type:", event)

replay.replay_input_event = dispatch_input_event

def handle(e):
	try:
		#it gets messed up so i make a throwaway copy and pickle the original
		dispatch_input_event(copy(e))
	finally:
		#log(pp(e))
		replay.add(e)

def send_thread_message():
	pygame.event.post(pygame.event.Event(pygame.USEREVENT + 2))

thread_message_signal = Signal(0)

def process_event(event):
	if event.type == pygame.USEREVENT:
		pass # we woke up python to poll for SIGINT

	elif event.type == pygame.USEREVENT + 1:
		c.editor.cursor_blink_phase = not c.editor.cursor_blink_phase

	elif event.type == pygame.USEREVENT + 2:
		thread_message_signal . emit ()

	elif event.type == pygame.KEYDOWN:
		handle(KeypressEvent(pygame.key.get_pressed(), event.unicode, event.key, event.mod))

	elif event.type == pygame.MOUSEBUTTONDOWN:
		handle(MousedownEvent(event))

	elif event.type == pygame.VIDEORESIZE:
		handle(ResizeEvent(event.size))

	elif event.type == pygame.ACTIVEEVENT:
		if event.gain:
			reset_cursor_blink_timer()
		else:
			pygame.time.set_timer(pygame.USEREVENT + 1, 0)#disable the timer
			c.editor.cursor_blink_phase = False
		redraw(666)

	elif event.type == pygame.QUIT:
		pygame.display.iconify()
		lemon_client.bye()




def redraw(self):
	for f in c.visibleframes():
		#log("maybe_redrawing %s on the client window request",f)
		f.maybe_draw()
	pygame.display.flip()
#lemon_client.draw = redraw
#all frames are in one window, so avoid signaling each about redrawing,
#hook into "aggregate" server.on_change instead
if not args.rpc:
	rpcing_frames.ClientFrame.redraw = redraw


def loop():
	process_event(pygame.event.wait())

def initial_resize():
	"""SDL insists that you must give your new window some size
	(screen_surface = pygame.display.set_mode), it ignores the WM
	but if the WM takes over...it doesnt even realize it!
	so it thinks it has the original size
	so i try to get the actual window size and "resize" """
	resize((666,666))
	try:
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
		resize(w, h)
	except Exception as e:
		info("%s, failed to work around stupid sdl, will continue thinking the window is 666x666, please do a manual resize", e)

def fix_keyboard():
	repeat_delay, repeat_rate = 300, 30
	try:#try to set SDL keyboard settings to system settings
		lines = subprocess.check_output(['xset', '-q']).split(b'\n')
		line = [line.split() for line in lines if "repeat delay" in line][0]
		#old: line = os.popen('xset -q  | grep "repeat delay"').read().split()
		repeat_delay, repeat_rate = int(line[3]), int(line[6])
	except Exception as e:
		print ("cant get system keyboard repeat delay/rate:", e)
	#print ("setting repeat delay to %s, repeat rate to %s" % (repeat_delay, repeat_rate))
	pygame.key.set_repeat(repeat_delay, 1000//repeat_rate)


def mainloop():
	while True:
		loop()


def main():
	global c
	display.set_caption('lemon operating language')
	try:
		icon = image.load('icon32x32.png')
		display.set_icon(icon)
	except:
		pass

	fix_keyboard()

	change_font_size()

	c = lemon_client.Client(thread_message_signal, send_thread_message)
	keybindings.c = c
	#for f in c.allframes:
	#	f.rect = pygame.Rect((6,6),(6,6))

	initial_resize()

	c.after_start()

	if args.no_timers:
		args.dontblink = True
	else:
		pygame.time.set_timer(pygame.USEREVENT, 777) #poll for SIGINT once in a while

	reset_cursor_blink_timer()

	try:
		if args.profile:
			import cProfile
			cProfile.run('mainloop()', filename="lemon.profile")
		else:
			mainloop()
	#	except KeyboardInterrupt() as e:
	#		pygame.display.iconify()
	#		raise e
	except Exception as e:
		#log(e),pass
		pygame.display.iconify()
		raise

if __name__ == "__main__":
	try:
		main()
	finally:
		if args.freetype:
			log("prepare for the segfault..")

