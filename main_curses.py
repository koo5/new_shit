#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
import curses as c
import sys

import lemon
from lemon import logframe, root, sidebars, allframes
from lemon import frames
import logger
from logger import log
from lemon_colors import colors, color
from lemon_six import iteritems
import lemon_args
from rect import Rect
import keys

args = lemon.args = lemon_args.parse_args()

logfile = open("curses_log", "w")

def debug_out(text):
	logframe.add(text)
	#print(text)
	logfile.write(text+"\n")
	logfile.flush()
logger.debug = debug_out

for f in allframes:
	f.rect = Rect(6,6,6,6)

def render():
	lemon.render()

def resize_frames():
	screen_height, screen_width = scr.getmaxyx()
	log("HW",screen_height, screen_width)

	lemon.logframe.rect.height = log_height = args.log_height
	lemon.logframe.rect.width = screen_width
	lemon.logframe.rect.topleft = (0, screen_height - log_height)

	lemon.root.rect.topleft = (0,0)
	lemon.root.rect.width = screen_width // 3 * 2
	lemon.root.rect.height = screen_height - log_height

	sidebar_rect = Rect((root.rect.w, 0),(0,0))
	sidebar_rect.width = screen_width - lemon. root.rect.width
	sidebar_rect.height = root.rect.height
	for frame in lemon.sidebars:
		frame.rect = sidebar_rect

	for f in allframes:
		f.cols = f.rect.width
		f.rows = f.rect.height

	for x,y in [(mainw, root), (logw, logframe), (sidebarw, lemon.sidebar)]:
		log("f",y, (y.rect.y, y.rect.x),(y.rows,y.cols))
		x.resize(y.rows,y.cols)
		x.mvwin(y.rect.y, y.rect.x)


def change_font_size():
	log ("nope")


def draw():
	if lemon.fast_forward:
		return

	#ok this is hacky
	#log("root")
	draw_lines(root, mainw, root.under_cursor)
	
	if isinstance(lemon.sidebar, frames.Menu):
		#log("menu")
		draw_lines(lemon.sidebar, sidebarw, lemon.sidebar.selected)
	else:
		#log("info")
		draw_lines(lemon.sidebar, sidebarw)
	
	#log("log")
	draw_lines(logframe, logw)
	
	for w in [mainw, sidebarw, logw]:
		w.refresh()
	scr.refresh()

def draw_lines(self, win, highlight=None):
		win.clear()
	#try:
		#log(self)
		for row, line in enumerate(self.lines):
			for col, char in enumerate(line):
				#log(row,col,":",ord(char[0]))
				if 'node' in char[1] and char[1]['node'] == highlight:
					mode = c.A_BOLD + c.A_REVERSE
				else:
					mode = 0
				try:
					win.addch(row,col,ord(char[0]), mode)
				except c.error:
					if (row+1, col+1) != win.getmaxyx():
						log(row,col,'of',  win.getmaxyx(),":",ord(char[0]))
						raise
					
#	except c.error as e:
#		pass

def bye():
	sys.exit()

curses2sdl = {
c.KEY_UP: keys.K_UP,
c.KEY_DOWN: keys.K_DOWN,
c.KEY_LEFT: keys.K_LEFT,
c.KEY_RIGHT: keys.K_RIGHT,
c.KEY_HOME: keys.K_HOME,
c.KEY_END: keys.K_END,
c.KEY_PPAGE: keys.K_PAGEUP,
c.KEY_NPAGE: keys.K_PAGEDOWN,
10: keys.K_RETURN,
c.KEY_BACKSPACE: keys.K_BACKSPACE,
c.KEY_END: keys.K_END}
#c.KEY_: keys.K_,

def loop():
	render()
	draw()
	inp = scr.getch(root.cursor_r,root.cursor_c)
	dummy_allkeys = [False]*(keys.K_MAX+1)
	if inp in curses2sdl:
		lemon.handle(lemon.KeypressEvent(dummy_allkeys, False, curses2sdl[inp], 0))
	else:
		lemon.handle(lemon.KeypressEvent(dummy_allkeys, unichr(inp), 0, 0))
	log(inp)

def main_func(stdscr):
	global scr, mainw, logw, sidebarw
	scr = stdscr
	scr.keypad(1)
	mainw = c.newwin(0,0,6,6)
	logw = c.newwin(0,0,6,6)
	sidebarw = c.newwin(0,0,6,6)

	resize_frames()

	lemon.change_font_size = change_font_size
	lemon.start()
	render()
	draw()

	while True:
		loop()

if __name__ == "__main__":
	try:
		c.wrapper(main_func)
	except Exception as e:
		log(e)
		logfile.flush()
		logfile.close()
		raise


#        stdscr.addstr(ypos[j],     xpos[j] - 1, "|.|")

#maybe we could use one of the enters for menu selection..in sdl too
#http://lists.gnu.org/archive/html/bug-ncurses/2011-01/msg00011.html
