#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from math import *

os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
import pygame
from pygame import display, image
from pygame import draw, Rect

import lemon
from lemon import logframe, root, sidebars, allframes
from lemon import frames
import logger
from logger import log
from lemon_colors import colors, color
from lemon_six import iteritems
import lemon_args

args = lemon.args = lemon_args.parse_args()


for f in allframes:
	f.rect = pygame.Rect((6,6),(6,6))

flags = pygame.RESIZABLE|pygame.DOUBLEBUF


def debug_out(text):
	print(text)
	logframe.add(text)

logger.debug = debug_out

def render():
	root.render()
	lemon.sidebar.render()
	logframe.render()
	#log("boing")
	if isinstance(lemon.sidebar, frames.Menu):
		menu_generate_rects(lemon.sidebar)

def reset_cursor_blink_timer():
	if not args.dontblink:
		pygame.time.set_timer(pygame.USEREVENT + 1, 800)
	root.cursor_blink_phase = True

def user_change_font_size(by = 0):
	change_font_size(by)
	resize_frames()

def change_font_size(by = 0):
	global font, font_width, font_height
	args.font_size += by
	font = pygame.font.SysFont('monospace', args.font_size)
	font_width, font_height = font.size("X")
	
def resize(size):
	global screen_surface, screen_width, screen_height
	log("resize to "+str(size))
	screen_surface = pygame.display.set_mode(size, flags)
	screen_width, screen_height = screen_surface.get_size()
	
def resize_frames():
	lemon.logframe.rect.height = log_height = 110
	lemon.logframe.rect.width = screen_width
	lemon.logframe.rect.topleft = (0, screen_height - log_height)

	lemon.root.rect.topleft = (0,0)
	lemon.root.rect.width = screen_width / 3 * 2
	lemon.root.rect.height = screen_height - log_height

	sidebar_rect = Rect((root.rect.w, 0),(0,0))
	sidebar_rect.width = screen_width - lemon. root.rect.width
	sidebar_rect.height = root.rect.height
	for frame in lemon.sidebars:
		frame.rect = sidebar_rect

	for f in allframes:
		f.cols = f.rect.width / font_width
		f.rows = f.rect.height / font_height
		



def keypress(e):
	reset_cursor_blink_timer()
	lemon.handle(lemon.KeypressEvent(e, pygame.key.get_pressed()))
	render()
	draw()

def mousedown(e):
	reset_cursor_blink_timer()
	#handle ctrl + mousewheel font changing
	if e.button in [4,5] and (
		pygame.key.get_pressed()[pygame.K_LCTRL] or
		pygame.key.get_pressed()[pygame.K_RCTRL]):
			if e.button == 4: change_font_size(1)
			if e.button == 5: change_font_size(-1)
	else:
		lemon.handle(lemon.MousedownEvent(e))
	render()
	draw()

def lemon_mousedown(e):
	for f in [logframe, lemon.sidebar, root]:
		if f.rect.collidepoint(e.pos):
			e.pos = (e.pos[0] - f.rect.x, e.pos[1] - f.rect.y)
			f.mousedown(e)
			break
lemon.mousedown = lemon_mousedown

def process_event(event):
	if event.type == pygame.USEREVENT:
		pass # we woke up python to poll for SIGINT

	elif event.type == pygame.USEREVENT + 1:
		root.cursor_blink_phase = not root.cursor_blink_phase
		draw()

	elif event.type == pygame.KEYDOWN:
		keypress(event)

	elif event.type == pygame.MOUSEBUTTONDOWN:
		mousedown(event)

	elif event.type == pygame.VIDEORESIZE:
		resize(event.size)
		resize_frames()
		render()

	elif event.type == pygame.ACTIVEEVENT:
		if event.gain:
			reset_cursor_blink_timer()
		else:
			pygame.time.set_timer(pygame.USEREVENT + 1, 0)#disable
			root.cursor_blink_phase = False
		draw()

	elif event.type == pygame.QUIT:
		bye()




def draw():
	if lemon.fast_forward:
		return
	#ok this is hacky
	surf = new_surface(root)
	root_draw(root, surf)
	screen_surface.blit(surf, root.rect.topleft)

	surf = new_surface(lemon.sidebar)
	if isinstance(lemon.sidebar, frames.Menu):
		menu_draw(lemon.sidebar, surf)
	else:
		info_draw(lemon.sidebar, surf)
	screen_surface.blit(surf, lemon.sidebar.rect.topleft)

	surf = new_surface(logframe)
	info_draw(logframe, surf)
	screen_surface.blit(surf, logframe.rect.topleft)

	pygame.display.flip()

def new_surface(self):
	surface = pygame.Surface((self.rect.w, self.rect.h), 0)
	if colors.bg != (0,0,0):
		surface.fill(colors.bg)
	return surface

def draw_lines(self, surf, highlight=None, transparent=False, justbg=False):
	bg_cached = color("bg")
	for row, line in enumerate(self.lines):
		for col, char in enumerate(line):
			x = font_width * col
			y = font_height * row
			bg = color("highlighted bg" if (
				'node' in char[1] and
				char[1]['node'] == highlight and
				not args.eightbit) else "bg")
			if justbg:
				if bg != bg_cached:
					pygame.draw.rect(surf,bg,(x,y,font_width,font_height))
			#	sur = font.render(' ',0,(0,0,0),bg)#guess i could just make a rectangle
			else:
				fg = color(char[1]['color'])
				if transparent:
					sur = font.render(char[0],1,fg)
				else:
					sur = font.render(char[0],1,fg,bg)
				surf.blit(sur,(x,y))

def draw_arrows(s, surface):
	for ((c,r),(c2,r2)) in s.arrows:
		x,y,x2,y2 = font_width * (c+0.5), font_height * (r+0.5), font_width * (c2+0.5), font_height * (r2+0.5)
		pygame.draw.line(surface, color("arrow"), (int(x),int(y)),(int(x2),int(y2)))
		a = atan2(y-y2, x-x2)
		angle = 0.1
		length = 40
		arrow_side(s, length, a+angle, x2,y2, surface)
		arrow_side(s, length, a-angle, x2,y2, surface)
			
def arrow_side(s, length,a,x2,y2, surface):
	x1y1 = int(length * cos(a) + x2), int(length * sin(a) + y2)
	pygame.draw.line(surface, color("arrow"), x1y1,(int(x2),int(y2)))

def root_draw(self, surf):
	if self.arrows_visible:
		draw_lines(self, surf, self.under_cursor, 666, True)
		draw_arrows(self, surf)
		draw_lines(self, surf, self.under_cursor, True)
	else:
		draw_arrows(self, surf)
		draw_lines(self, surf, self.under_cursor, False)
	draw_cursor(self, surf)

def draw_cursor(self, surf):
	if self.cursor_blink_phase:
		x, y, y2 = self.cursor_xy()
		pygame.draw.rect(surf, colors.cursor, (x, y, 1, y2 - y,))

def menu_draw(s, surface):
	draw_lines(s, surface)
	draw_rects(s, surface)

def draw_rects(s, surface):
	for i,r in iteritems(s.rects):
		if i == s.selected:
			c = colors.menu_rect_selected
		else:
			c = colors.menu_rect
		pygame.draw.rect(surface, c, r, 1)

def info_draw(s, surface):
	draw_lines(s, surface)

def menu_generate_rects(s):
	s.rects = dict()
	for i in s.items_on_screen:
		rl = i._render_lines[s]

		startline = rl["startline"] - s.scroll_lines if "startline" in rl else 0
		endline = rl["endline"]  - s.scroll_lines if "endline" in rl else s.rows

		if endline < 0 or startline > s.rows:
			continue
		if startline < 0:
			startline = 0
		if endline > s.rows - 1:
			endline = s.rows - 1

		startchar = 0
		#print startline, endline+1
		endchar = max([len(l) for l in s.lines[startline:endline+1]])
		r = (startchar * font_width,
		     startline * font_height,
		     (endchar  - startchar) * font_width,
		     (endline - startline+1) * font_height)
		s.rects[i] = r


def bye():
	log("deading")
	pygame.display.iconify()
	sys.exit()

def loop():
	process_event(pygame.event.wait())

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


def main():

	pygame.display.init()
	pygame.font.init()
	display.set_caption('lemon operating language v'+str(lemon.version))
	icon = image.load('icon32x32.png')
	display.set_icon(icon)

	resize((666,666))
	try:
		resize(fuck_sdl())
	except Exception as e:
		print (e, "failed to work around stupid sdl, will continue thinking the window is 666x666, please do a manual resize")

	repeat_delay, repeat_rate = 300, 30
	try:#try to set SDL keyboard settings to system settings
		s = os.popen('xset -q  | grep "repeat delay"').read().split()
		repeat_delay, repeat_rate = int(s[3]), int(s[6])
	except Exception as e:
		print ("cant get system keyboard repeat delay/rate:", e)
	pygame.key.set_repeat(repeat_delay, 1000/repeat_rate)
	pygame.time.set_timer(pygame.USEREVENT, 777) #poll for SIGINT once in a while

	change_font_size()
	resize_frames()
	lemon.change_font_size = user_change_font_size
	lemon.start()
	render()

	pygame.time.set_timer(pygame.USEREVENT, 777) #poll for SIGINT once in a while
	reset_cursor_blink_timer()

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
