#!/usr/bin/python
# -*- coding: utf-8 -*-




import argparse, sys, os

os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
import pygame
from pygame import display, image


from logger import log
import project
import colors
import frames




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

def resize_frames():
	root.rect.topleft = (0,0)
	root.rect.width = screen_width / 3 * 2
	root.rect.height = screen_height
	menu.rect.topleft = (root.rect.w, 0)
	info_height = min(info.used_height, screen_height / 2)
	menu.rect.size = (screen_width - root.rect.width, screen_height - info_height)
	info.rect.topleft = (root.rect.w, menu.rect.h)
	info.rect.size = (menu.rect.width,	info_height)


def top_keypress(event):
	global cursor_r,cursor_c
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

replay = []
import pickle, copy

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
		do_keypress(copy.deepcopy(i))
	fast_forward = False



def keypress(event):
	reset_cursor_blink_timer()
	e = KeypressEvent(event)
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
		do_keypress(copy.deepcopy(e))

def do_keypress(e):
	top_keypress(e) or menu.on_keypress(e) or root.on_keypress(e)
	render()


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
		for f in all_frames:
			if f.rect.collidepoint(e.pos):
				pos = (e.pos[0] - f.rect.x, e.pos[1] - f.rect.y)
				f.mousedown(e, pos)
				render()
				break


def process_event(event):

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
		resize(event.dict['size'])
		render()


def reset_cursor_blink_timer():
	pygame.time.set_timer(pygame.USEREVENT + 1, 800)
	root.cursor_blink_phase = True



def render():
	root.render()
	info.render()
	resize_frames()
	menu.render(root)
	draw()


def draw():
	if not fast_forward:
		screen_surface.blit(root.draw(),root.rect.topleft)
		screen_surface.blit(menu.draw(),menu.rect.topleft)
		screen_surface.blit(info.draw(),info.rect.topleft)
		pygame.display.flip()

def bye():
	log("deading")
	pygame.display.iconify()
	sys.exit()

def loop():
	process_event(pygame.event.wait())





parser = argparse.ArgumentParser()
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
args = parser.parse_args()


pygame.display.init()
pygame.font.init()


#try to set SDL keyboard settings to system settings
s = os.popen('xset -q  | grep "repeat delay"').read().split()
repeat_delay, repeat_rate = int(s[3]), int(s[6])
pygame.key.set_repeat(repeat_delay, 1000/repeat_rate)
flags = pygame.RESIZABLE|pygame.DOUBLEBUF
screen_surface = None
display.set_caption('lemon operating language v 0.0 streamlined insane prototype with types')
icon = image.load('icon32x32.png')
display.set_icon(icon)

change_font_size()
colors.cache(args)

root = frames.Root()
menu = frames.Menu()
menu.root = root
info = frames.Info()
info.root = root
all_frames = [root, menu, info]
fast_forward = False

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
except:
	print "failed to work around stupid sdl, will continue thinking the window is 666x666, please do a manual resize"


root.render()
try:
	root.cursor_c, root.cursor_r = project.find(root.root['program'].ch.statements.items[0], root.lines)
	root.cursor_c += 1
except Exception as e:
	print e, ", cant move cursor"


if args.replay:
	do_replay(True)
render()


pygame.time.set_timer(pygame.USEREVENT, 100) #poll for SIGINT
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
