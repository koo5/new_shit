#!/usr/bin/python
# -*- coding: utf-8 -*-

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

args = lemon.args = lemon_args.parse_args()

logfile = open("curses_log", "w")

def debug_out(text):
	logframe.add(text)
	#print(text)
	logfile.write(text+"\n")
logger.debug = debug_out

for f in allframes:
	f.rect = Rect(6,6,6,6)

def render():
	root.render()
	lemon.sidebar.render()
	logframe.render()

def resize_frames():
	screen_height, screen_width = scr.getmaxyx()
	log(screen_height, screen_width)

	lemon.logframe.rect.height = log_height = 4
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
		f.cols = f.rect.width
		f.rows = f.rect.height

	for x,y in [(mainw, root), (logw, logframe), (sidebarw, lemon.sidebar)]:
		log(y, (y.rect.y, y.rect.x),(y.rows,y.cols))
		x.resize(y.rows,y.cols)
		x.mvwin(y.rect.y, y.rect.x)


def change_font_size():
	log ("nope")


def draw():
	if lemon.fast_forward:
		return
	#ok this is hacky
	log("root")
	draw_lines(root, mainw, root.under_cursor)
	
	
	if isinstance(lemon.sidebar, frames.Menu):
		log("menu")
		draw_lines(lemon.sidebar, sidebarw, lemon.sidebar.selected)
	else:
		log("info")
		info_draw(lemon.sidebar, sidebarw)
	
	log("log")
	draw_lines(logframe, logw)
	
	for w in [mainw, sidebarw, logw]:
		w.refresh()
	scr.refresh()

def draw_lines(self, win, highlight=None):
	try:
		for row, line in enumerate(self.lines):
			for col, char in enumerate(line):
				log(row,col,ord(char[0]))
				win.addch(row,col,ord(char[0]))
	except:
		pass

def bye():
	sys.exit()

def loop():
	render()
	draw()
	inp = scr.getch()
	if inp == ord('q'):
		bye()


def main_func(stdscr):
	global scr, mainw, logw, sidebarw
	scr = stdscr

	mainw = c.newwin(0,0,6,6)
	logw = c.newwin(0,0,6,6)
	sidebarw = c.newwin(0,0,6,6)

	resize_frames()

	lemon.change_font_size = change_font_size
	lemon.start()

	while True:
		loop()

if __name__ == "__main__":
	try:
		c.wrapper(main_func)
	except Exception as e:
		log(e)
		logfile.close()
		raise


#        stdscr.addstr(ypos[j],     xpos[j] - 1, "|.|")

