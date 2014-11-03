#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import division

import curses as c
import sys

import lemon_platform as platform
platform.frontend = platform.curses
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
import nodes


def debug_out(text):
	logframe.add(text)
	#print(text)
	logfile.write(text+"\n")
	logfile.flush()
logger.debug = debug_out

for f in allframes:
	f.rect = Rect(6,6,6,6)

def render():
	root.render()
	lemon.sidebar.render()
	logframe.render()
lemon.render = render # for replays and stuff

def resize_frames():
	screen_height, screen_width = scr.getmaxyx()
	log("HW",screen_height, screen_width)

	lemon.logframe.rect.height = log_height = args.log_height
	lemon.logframe.rect.width = screen_width
	lemon.logframe.rect.topleft = (0, screen_height - log_height)

	lemon.root.rect.topleft = (0,0)
	lemon.root.rect.width = screen_width // 3 * 2
	lemon.root.rect.height = screen_height - log_height

	sidebar_rect = Rect((root.rect.w+1, 0),(0,0))
	sidebar_rect.width = screen_width - root . rect . width -1
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
lemon.draw = draw

def draw_lines(self, win, highlight=None):
		win.clear()
	#try:
		#log(self)
		for row, line in enumerate(self.lines):
			for col, char in enumerate(line):
				#log(row,col,":",ord(char[0]))
				#if isinstance(self, frames.Menu):
				#	if 'node' in char[1]:
				#		log(char[1]['node'], '==', highlight)
				#blehhack
				#if (isinstance(highlight, (nodes.ParserMenuItem,
				#	nodes.LeshMenuItem)) and
				#'node' in char[1] and char[1]['node'] == highlight.value):

				mode = 0
				try:
					if char[1]['node'] == highlight:
						mode = c.A_BOLD + c.A_REVERSE
				except:
					pass

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
27: keys.K_ESCAPE,
c.KEY_BACKSPACE: keys.K_BACKSPACE,
c.KEY_END: keys.K_END,
c.KEY_IC: keys.K_INSERT,
c.KEY_DC: keys.K_DELETE,
c.KEY_F1: keys.K_F1,
c.KEY_F2: keys.K_F2,
c.KEY_F3: keys.K_F3,
c.KEY_F4: keys.K_F4,
c.KEY_F5: keys.K_F5,
c.KEY_F6: keys.K_F6,
c.KEY_F7: keys.K_F7,
c.KEY_F8: keys.K_F8,
c.KEY_F9: keys.K_F9,
c.KEY_F10: keys.K_F10,
c.KEY_F11: keys.K_F11,
c.KEY_F12: keys.K_F12}
#c.KEY_: keys.K_,
#oh...unfinished..
def loop():

	render()
	draw()
	inp = scr.getch(root.cursor_r,root.cursor_c)
	dummy_allkeys = [False]*(keys.K_MAX+1)
	if inp in curses2sdl:
		lemon.handle(lemon.KeypressEvent(dummy_allkeys, False, curses2sdl[inp], 0))
	else:
		lemon.handle(lemon.KeypressEvent(dummy_allkeys, unichr(inp), 0, 0))
	log(inp, c.unctrl(inp))

def main_func(stdscr, replay):
	global scr, mainw, logw, sidebarw, args, logfile
	scr = stdscr
	scr.keypad(1)
	mainw = c.newwin(0,0,6,6)
	logw = c.newwin(0,0,6,6)
	sidebarw = c.newwin(0,0,6,6)

	args = lemon_args.parse_args()
	if replay:
		args.replay = True
	lemon.args = args
	logfile = open("curses_log", "w")

	resize_frames()

	lemon.change_font_size = change_font_size
	lemon.root.arrows_visible = False
	lemon.start()

	render()
	draw()

	while True:
		loop()

def main(replay = False):
	try:
		c.wrapper(main_func, replay)
	except Exception as e:
		log(e)
		logfile.flush()
		logfile.close()
		raise

if __name__ == "__main__":
    main()

# __________  Entry point  __________
#just playing with rpython..
def entry_point(argv):
    main()
    return 0

# _____ Define and setup target ___

def target(*args):
    return entry_point, None


#        stdscr.addstr(ypos[j],     xpos[j] - 1, "|.|")

#maybe we could use one of the enters for menu selection..in sdl too
#http://lists.gnu.org/archive/html/bug-ncurses/2011-01/msg00011.html
