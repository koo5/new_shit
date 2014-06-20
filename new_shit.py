#!/usr/bin/python
# -*- coding: utf-8 -*-


import argparse, sys, os


import pygame
from pygame import display, image


from logger import log
import project
import colors
import frames




def change_font_size():
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
	root.rect.width = screen_width / 2
	root.rect.height = screen_height
	menu.rect.topleft = (root.rect.w, 0)
	info_height = min(info.used_height, screen_height / 2)
	menu.rect.size = (screen_width / 2, screen_height - info_height)
	info.rect.topleft = (root.rect.w, menu.rect.h)
	info.rect.size = (screen_width / 2,	info_height)

def top_keypress(event):
	global cursor_r,cursor_c
	k = event.key

	if pygame.KMOD_CTRL & event.mod:
		if event.uni == '=':
			args.font_size += 1
			change_font_size()
		elif event.uni == '-':
			args.font_size -= 1
			change_font_size()
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

def keypress(event):
	global replay
	e = KeypressEvent(event)

	if e.key == pygame.K_F2:
		try:
			with open("replay.p", "rb") as f:
				replay = pickle.load(f)
		except:
			log("couldnt read replay.p")
			replay = []
		for i in replay:
			do_keypress(copy.deepcopy(i))
	else:
		if e.key == pygame.K_ESCAPE:
			bye()
		else:
			replay.append(e)
			with open("replay.p", "wb") as f:
				#print replay
				try:
					pickle.dump(replay, f)
				except pickle.PicklingError as error:
					print error, ", are you profiling?"
		do_keypress(copy.deepcopy(e))

def do_keypress(e):
	top_keypress(e) or menu.on_keypress(e) or root.on_keypress(e)
	draw()


def mousedown(e):
	for f in all_frames:
		if f.rect.collidepoint(e.pos):
			pos = (e.pos[0] - f.rect.x, e.pos[1] - f.rect.y)
			f.mousedown(e, pos)
			draw()
			break

def process_event(event):

	if event.type == pygame.QUIT:
		bye()

	if event.type == pygame.KEYDOWN:
		keypress(event)

	if event.type == pygame.MOUSEBUTTONDOWN:
		mousedown(event)

	if event.type == pygame.VIDEORESIZE:
		resize(event.dict['size'])
		draw()



def draw():
	root.render()
	info.render()
	resize_frames()
	menu.update(root)
	menu.render()
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
				   default=28)
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
info = frames.Info()
all_frames = [root, menu, info]


def fuck_sdl():
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
root.cursor_c, root.cursor_r = project.find(root.root['program'].ch.statements.items[0].items[0], root.lines)
root.cursor_c += 1


draw()


pygame.time.set_timer(pygame.USEREVENT, 100) #poll for SIGINT
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
