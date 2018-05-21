#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, sys
import subprocess
from math import *
from pprint import pformat as pp
from copy import copy
import traceback


#from pizco import Signal
from lemon_utils.pizco_signal.util import Signal


from lemon_utils.lemon_six import iteritems
from lemon_utils.utils import Evil
import lemon_utils.lemon_logging
import logging
logger=logging.getLogger("root")
log=logger.debug
info=logger.info


import lemon_args


lemon_args.parse_args()
from lemon_args import args

if args.kbdbg:
	args.lame = args.arrows = True


from frontend_events import *


os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'


from pygame_wrapper import pygame

from pygame import display, image, Rect, time
flags = pygame.RESIZABLE#|pygame.DOUBLEBUF


display.init()
from pygame import freetype
freetype.init(cache_size=1024)


import lemon_platform
lemon_platform.SDL = True


import ui_generic_lemon_client, rpcing_frames
import keybindings
import replay

from rpcing_frames import Font, Line





fonts = {}
font_size_step = 10

def user_change_font_size(by = 0):
	change_font_size(by)
	resize_frames()
	redraw_all()
keybindings.change_font_size = user_change_font_size

def get_font(level):
	if not args.multiple_fonts:
		level = 0
	size = (level * font_size_step) + args.font_size
	if size not in fonts:
		fonts[size] = make_font(size)
	return fonts[size]
rpcing_frames.get_font = get_font

def make_font(size):
	font = freetype.SysFont('monospace', size)
	#font.origin = True
	_, _, w, _ = font.get_rect("X")
	h = font.get_sized_glyph_height()
	#for x in ['X', 'x', ':', 'rstartsiu#$#$TS', ',']:
	#	log(font.get_rect(x))

	return Font(font, w, h)

def change_font_size(by = 0):
	args.font_size += by
	if args.font_size < 1:
		args.font_size = 1
	info("font size:%s", args.font_size)





def resize(size):
	global screen_surface, screen_width, screen_height
	log("resize to "+str(size))
	rpcing_frames.sdl_screen_surface = screen_surface = pygame.display.set_mode(size, flags)
	screen_width, screen_height = screen_surface.get_size()
	resize_frames()
	redraw_all(555)
replay.resize = resize

def resize_frames():
		c.logframe.rect = Rect (
			0, screen_height - args.log_height,
			screen_width, args.log_height * get_font(0).height) # log frame uses default font

		if args.kbdbg:
			ew = screen_width
		else:
			ew = screen_width // 3 * 2


		c.editor.rect = Rect(0,0,
			ew,
			screen_height - c.logframe.rect.height)

		sidebar_rect = Rect(c.editor.rect.w, 0,
		    screen_width - c.editor.rect.width,
			c.editor.rect.height)

		for frame in c.sidebars:
			frame.rect = sidebar_rect

		log("resized frames")





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
	def do_it():
		try:
			#e gets messed up so i use a throwaway copy inside the handlers and pickle the original
			dispatch_input_event(copy(e))
		finally:
			#log(pp(e))
			replay.add(e)
	if args.crash:
		do_it()
	else:
		try:
			do_it()
		except Exception:
			traceback.print_exc(file=sys.stdout)


def process_event(event):
	if event.type == pygame.USEREVENT:
		pass # we woke up python to poll for SIGINT

	elif event.type == pygame.USEREVENT + 1:
		c.editor.cursor_blink_phase = not c.editor.cursor_blink_phase

	elif event.type == pygame.USEREVENT + 2:
		thread_message_signal . emit ()

	elif event.type == pygame.USEREVENT + 3:
		c.menu.counterpart.update_menu()

	elif event.type == pygame.USEREVENT + 4:
		on_rpc_message()

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
		redraw_all(666)

	elif event.type == pygame.QUIT:
		pygame.display.iconify()
		ui_generic_lemon_client.bye()





def redraw_all(self=None):
	for f in c.visibleframes():
		#log("maybe_redrawing %s on client window request",f)
		f.maybe_draw()
	pygame.display.flip()
	ui_generic_lemon_client.redraw = redraw_all

def redraw(self):
	self.maybe_draw()
	pygame.display.update(self.rect)
rpcing_frames.ClientFrame.maybe_redraw = redraw





def initial_resize():
	"""SDL insists that you must give your new window some size
	(screen_surface = pygame.display.set_mode), it ignores the WM
	but if the WM forces a size...it doesnt even realize it!
	so it thinks it has the original size
	so i try to get the actual window size and "resize" """
	resize((666,666))
	try:
		w = pygame.display.get_wm_info()["wmwindow"]
		import subprocess
		x =  subprocess.check_output(["xwininfo", "-id", str(w)]).decode()
		y = x.splitlines()
		for l in y:
			s = l.split()
			if len(s) > 1:
				if s[0] == "Width:":
					w = int(s[1])
				if s[0] == "Height:":
					h = int(s[1])
		resize((w, h))
	except Exception as e:
		info("%s, failed to work around stupid sdl, will continue thinking the window is 666x666, please do a manual resize", e)


#db_worthy
def set_pygame_keyboard_settings_to_system_settings():
	"""
	pygame 1, unix
	"""
	repeat_delay, repeat_rate = 300, 30
	try:#try to set SDL keyboard settings to system settings
		lines = subprocess.check_output(['xset', '-q']).decode().splitlines()
		lines = [line.split() for line in lines if "repeat delay" in line]
		line = lines[0]
		#old: line = os.popen('xset -q  | grep "repeat delay"').read().split()
		repeat_delay, repeat_rate = int(line[3]), int(line[6])
	except Exception as e:
		print ("cant get system keyboard repeat delay/rate:", e)
	info ("setting repeat delay to %s, repeat rate to %s" % (repeat_delay, repeat_rate))
	pygame.key.set_repeat(repeat_delay, 1000//repeat_rate)
#end




def send_thread_message(offset = 2):
	pygame.event.post(pygame.event.Event(pygame.USEREVENT + offset))

thread_message_signal = Signal(0)

def reset_cursor_blink_timer():
	if not args.dontblink:
		pygame.time.set_timer(pygame.USEREVENT + 1, 1600)
	c.editor.cursor_blink_phase = True

def pygame_keypressevent__repr__(self):
		#a better repr that translates keys to key names
		return ("KeypressEvent(key=%s, uni=%s, mod=%s)" %
			(pygame.key.name(self.key), self.uni, bin(self.mod)))
KeypressEvent.__repr__ = pygame_keypressevent__repr__

rpcing_frames.server.key_to_name = pygame.key.name
rpcing_frames.server.mods_to_str = mods_to_str


def loop():
	process_event(pygame.event.wait())



from jsonrpc import Dispatcher, JSONRPCResponseManager, dispatcher
from jsonrpc.manager import JSONRPCRequest
import socketserver


dispatcher2 = Dispatcher()
from queue import Queue
rpc_message_queue = Queue()

import json

class MyTCPHandler(socketserver.StreamRequestHandler):
	def handle(self):
		data = b''
		while True:
			data += self.rfile.read1(1)
			try:
				json.loads(data.decode("utf-8"))
			except (TypeError, ValueError) as e:
				continue
			print("{} wrote:".format(self.client_address[0]))
			response = handle_sync_message(data)
			if 'error' in response:
				rpc_message_queue.append(self.data)
				send_thread_message(4)
				response = {"jsonrpc": "2.0",'result':'ok'}
			r = json.dumps(response).encode("utf-8")
			print(r)
			self.wfile.write(r)#\\"}}}}
			break

def handle_sync_message(data):
	print(data)
	response = JSONRPCResponseManager.handle(data, dispatcher)
	return response.data



def on_async_rpc_message():
	request_str = rpc_message_queue.pop()
	request_str = request_str.decode("utf-8")
	data = json.loads(request_str)
	request = JSONRPCRequest.from_data(data)
	method = dispatcher2[request.method]
	method(*request.args, **request.kwargs)



@dispatcher.add_method
def foobar(**kwargs):
	return kwargs["foo"] + kwargs["bar"]
dispatcher["echo"] = lambda s: s
dispatcher["add"] = lambda a, b: a + b




def _parse_sync(p, text=None):
	m = MarpaClient(print, True)
	m.clear()
	m.collect_grammar(p.full_scope(), p.scope(), p.type)  # parsed_symbol)
	m.enqueue_precomputation(None)
	while True:
		msg = m.t.output.get()
		if msg.message == 'precomputed':
			ts = m.string2tokens(text)
			print("tokens", ts)
			m.enqueue_parsing([ts, text])
		elif msg.message == 'parsed':
			return msg.results
		else:
			raise Exception(msg.message)

@dispatcher2.add_method
def menu(text):
	p = nodes.Parser()
	server_frames.editor.root.repl.ch.statements.add(p)
	server_frames.menu.current_parser_node = p
	server_frames.menu.update_menu()

@dispatcher2.add_method
def parse(text):
	if text == "":
		return False
	module = r['repl']
	p = nodes.Parser()
	module.ch.statements.add(p)
	p.add(nodes.Text(value=text))
	rr = _parse_sync(p, text)
	result = {}
	results = []
	result["results"] = results
	if (rr and len(rr)):
		for i in rr:
			print("parse result:%s" % i)
			if isinstance(i, nodes.Element):
				print(" - %s" % i.tostr())
			results.append({"value":i.serialize()})
	return result







def mainloop():
	while True:
		loop()


def init_rpc():

	#just for quicker debugging
	#handle_message(' {"id": null, "jsonrpc": "2.0", "method":"menu", "params":["pri"]}')
	#handle_message(' {"id": null, "jsonrpc": "2.0", "method":"parse", "params":["pri"]}')
	#handle_message(' {"id": null, "jsonrpc": "2.0", "method":"execute", "params":[{...}]}')


	HOST, PORT = "localhost", 9999

	def test():
		nonlocal HOST, PORT
		while True:
			try:
				server = socketserver.ThreadingTCPServer((HOST, PORT), MyTCPHandler)
				server.timeout = 0.01
				server.handle_request()
			except:# (OSError, ValueError)
				PORT += 1
				continue
			with server:
				print("listening on %s : %s" % (HOST, PORT))
				server.serve_forever()
				break

	import threading

	thread = threading.Thread(target=test)
	thread.daemon = True
	thread.start()



def main():
	global c
	display.set_caption('lemon operating language')
	try:
		icon = image.load('icon32x32.png')
		display.set_icon(icon)
	except:
		pass
	set_pygame_keyboard_settings_to_system_settings()
	change_font_size()
	c = ui_generic_lemon_client.Client(thread_message_signal, send_thread_message)
	keybindings.setup(c)
	initial_resize()
	c.after_start()
	if args.no_timers:
		args.dontblink = True
	else:
		pygame.time.set_timer(pygame.USEREVENT, 777) #poll for SIGINT once in a while
	reset_cursor_blink_timer()
	init_rpc()
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
	main()
