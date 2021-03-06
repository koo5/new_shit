#!/usr/bin/python3
# -*- coding: utf-8 -*-


import sys

import curses as c

import lemon_platform as platform
platform.frontend = platform.curses

from lemon_args import args
args.rpc = True

import lemon_utils.lemon_logging
from lemon_utils.lemon_logging import log

import keys

from server_side import server
import rpcing_frames

"""
def logging_handler(msg):
	server.log_add(msg)

log("setting logger.debug to server.log_add")
server.log_on_add.connect(logging_printer)
lemon_utils.lemon_logging.debug = logging_handler
"""

def resize_frame():
	rows, cols = scr.getmaxyx()
	log("H:%s W:%s"%(rows, cols))

	window.resize(rows, cols)

	frame.rows = rows
	frame.cols = cols


def change_font_size_dummy():
	log ("nope")


def draw():
	frame.draw()
	window.refresh()
	scr.refresh()

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

	draw()
	inp = scr.getch(root.cursor_r,root.cursor_c)
	dummy_allkeys = [False]*(keys.K_MAX+1)#curses wont tell us what other keys are pressed at any moment
	if inp in curses2sdl:
		lemon.handle(lemon.KeypressEvent(dummy_allkeys, False, curses2sdl[inp], 0))
	else:
		lemon.handle(lemon.KeypressEvent(dummy_allkeys, unichr(inp), 0, 0))
	log(inp, c.unctrl(inp))

def main_func(stdscr, replay):
	global scr, window, logw, sidebarw, args, logfile
	scr = stdscr
	scr.keypad(1)
	window = c.newwin(0,0,6,6)
	resize_frames()

	while True:
		loop()

def main(replay = False):
	try:
		c.wrapper(main_func, replay)
	except Exception as e:
		log(e)
		raise

if __name__ == "__main__":
    main()


