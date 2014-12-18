#!/usr/bin/python3
# -*- coding: utf-8 -*-


import os, sys
import subprocess
from math import *


from lemon_utils.lemon_six import iteritems
from lemon_utils.utils import Evil
from lemon_utils.lemon_logging import log, info
from lemon_colors import colors, color


import lemon_args
lemon_args.parse_args()
from lemon_args import args


os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
if hasattr(sys, 'pypy_version_info'):
	print ("trying to load pygame_cffi, adding pygame_cffi to sys.path")
	sys.path.append("pygame_cffi")
import pygame
if hasattr(pygame, 'cffi'):
	print("yep, loaded pygame_cffi")
from pygame import display, image
from pygame import draw, Rect
flags = pygame.RESIZABLE|pygame.DOUBLEBUF


import lemon_platform
lemon_platform.SDL = True


import lemon_client, rpcing_frames
from lemon_client import logframe, editor, allframes, visibleframes, sidebars
from server_side import server
import keybindings
import replay



for f in allframes:
	f.rect = pygame.Rect((6,6),(6,6))


"""
def render():
	root.render()
	lemon.sidebar.render()
	logframe.render()
	#log("boing")
	if isinstance(lemon.sidebar, frames.Menu):
		menu_generate_rects(lemon.sidebar)
"""



def reset_cursor_blink_timer():
	if not args.dontblink:
		pygame.time.set_timer(pygame.USEREVENT + 1, 1600)
	editor.cursor_blink_phase = True




def user_change_font_size(by = 0):
	change_font_size(by)
	resize_frames()
keybindings.change_font_size = user_change_font_size


def change_font_size(by = 0):
	global font, font_width, font_height
	args.font_size += by
	rpcing_frames.font = font = pygame.font.SysFont('monospace', args.font_size)
	rpcing_frames.font_width, rpcing_frames.font_height = font_width, font_height = font.size("X")


def resize(size):
	global screen_surface, screen_width, screen_height
	log("resize to "+str(size))
	rpcing_frames.sdl_screen_surface = screen_surface = pygame.display.set_mode(size, flags)
	screen_width, screen_height = screen_surface.get_size()
	resize_frames()
replay.resize = resize

def resize_frames():
		logframe.rect.height = log_height = args.log_height * font_height
		logframe.rect.width = screen_width
		logframe.rect.topleft = (0, screen_height - log_height)

		editor.rect.topleft = (0,0)
		editor.rect.width = screen_width // 3 * 2
		editor.rect.height = screen_height - log_height

		sidebar_rect = Rect((editor.rect.w, 0),(0,0))
		sidebar_rect.width = screen_width - editor.rect.width
		sidebar_rect.height = editor.rect.height
		for frame in sidebars:
			frame.rect = sidebar_rect

		for f in allframes:
			f.cols = f.rect.width // font_width
			f.rows = f.rect.height // font_height
			log((f, f.cols, f.rows))

		log("resized frames")



def pygame_keypressevent__repr__(self):
		#a better repr that translates keys to key names
		return ("KeypressEvent(key=%s, uni=%s, mod=%s)" %
			(pygame.key.name(self.key), self.uni, bin(self.mod)))
lemon_client.KeypressEvent.__repr__ = pygame_keypressevent__repr__


def keypress(e):
	reset_cursor_blink_timer()
	keybindings.keypress(e)
#	render()
	draw()

def mousedown(e):
	reset_cursor_blink_timer()
	#handle ctrl + mousewheel font changing
	if e.button in [4,5] and (
		pygame.key.get_pressed()[pygame.K_LCTRL] or
		pygame.key.get_pressed()[pygame.K_RCTRL]):
			if e.button == 4: user_change_font_size(1)
			if e.button == 5: user_change_font_size(-1)
	else:
		for f in lemon_client.visibleframes():
			if f.rect.collidepoint(e.pos):
				e.pos = (e.pos[0] - f.rect.x, e.pos[1] - f.rect.y)
				f.sdl_mousedown(e)
				break
#	render()
	draw()



def handle_input(event):
	if event.type == pygame.KEYDOWN:
		keypress(event)
		return True

	elif event.type == pygame.MOUSEBUTTONDOWN:
		mousedown(event)
		return True

def process_event(event):
	if event.type == pygame.USEREVENT:
		pass # we woke up python to poll for SIGINT

	elif event.type == pygame.USEREVENT + 1:
		editor.cursor_blink_phase = not editor.cursor_blink_phase
		draw()

	elif event.type == pygame.KEYDOWN:
		e = lemon_client.KeypressEvent(pygame.key.get_pressed(), event.unicode, event.key, event.mod)
		handle_input(e)
		replay.pickle_event(e)

	elif event.type == pygame.MOUSEBUTTONDOWN:
		e = lemon_client.MousedownEvent(event)
		handle_input(e)
		replay.pickle_event(e)

	elif event.type == pygame.VIDEORESIZE:
		replay.pickle_event(('resize', event.size))
		resize(event.size)
#		render()
		draw()

	elif event.type == pygame.ACTIVEEVENT:
		if event.gain:
			reset_cursor_blink_timer()
		else:
			pygame.time.set_timer(pygame.USEREVENT + 1, 0)#disable the timer
			editor.cursor_blink_phase = False
		draw()

	elif event.type == pygame.QUIT:
		pygame.display.iconify()
		lemon_client.bye()




def draw():
	for f in lemon_client.visibleframes():
		log("drawing %s",f)
		f.draw()
	pygame.display.flip()
#all frames are in one window, so avoid signaling each about redrawing,
#instead, hook into "aggregate" server.on_change
server.on_change.connect(draw)












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


def main():
	lemon_client.setup()

	pygame.display.init()
	pygame.font.init()
	display.set_caption('lemon operating language')
	try:
		icon = image.load('icon32x32.png')
		display.set_icon(icon)
	except:
		pass

	fix_keyboard()

	change_font_size()

	initial_resize()

	resize_frames()
	keybindings.change_font_size = user_change_font_size
	lemon_client.draw = draw

	lemon_client.start()
	#render()

	pygame.time.set_timer(pygame.USEREVENT, 777) #poll for SIGINT once in a while
	reset_cursor_blink_timer()

	while True:
		try:
			loop()
	#	except KeyboardInterrupt() as e:
	#		pygame.display.iconify()
	#		raise e
		except Exception as e:
			#log(e),pass
			pygame.display.iconify()
			raise

if __name__ == "__main__":
	main()
