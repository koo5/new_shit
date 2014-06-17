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
	log("resize")
	screen_surface = pygame.display.set_mode(size, flags)
	screen_width, screen_height = screen_surface.get_size()
	resize_frames()

def resize_frames():
	root.rect.topleft = (0,0)
	root.rect.width = screen_width / 2
	root.rect.height = screen_height
	menu.rect.topleft = (root.rect.w, 0)
	menu.rect.size = (screen_width / 2, screen_height - info.used_height)
	info.rect.topleft = (root.rect.w, menu.rect.h)
	info.rect.size = (screen_width / 2,	info.used_height)



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


def keypress(event):
	e = KeypressEvent(event)
	if top_keypress(e):
		return
	if menu.keypress(e):
		return
	root.keypress(e)


def mousedown(e):
	for f in frames:
		if f.rect.collidepoint(e.pos):
			e.pos.x -= f.rect.x
			e.pos.y -= f.rect.y
			f.mousedown(e)
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
				   default=18)
args = parser.parse_args()


pygame.display.init()
pygame.font.init()


#try to set SDL keyboard settings to system settings
s = os.popen('xset -q  | grep "repeat delay"').read().split()
repeat_delay, repeat_rate = int(s[3]), int(s[6])
pygame.key.set_repeat(repeat_delay, 1000/repeat_rate)
flags = pygame.RESIZABLE|pygame.DOUBLEBUF
screen_surface = None
display.set_caption('lemon v 0.0 streamlined insane prototype with types')
icon = image.load('icon32x32.png')
display.set_icon(icon)

change_font_size()
colors.cache(args)

root = frames.Root()
menu = frames.Menu()
info = frames.Info()
frames = [root, menu, info]

resize((1280,500))



root.render()

root.cursor_c, root.cursor_r = project.find(root.root['program'].ch.statements.items[0].items[0], root.lines)
root.cursor_c += 1


menu.update(root)
draw()


pygame.time.set_timer(pygame.USEREVENT, 100) #poll for SIGINT
def main():
	while True:
		try:
			loop()
	#	except KeyboardInterrupt() as e:
	#		pygame.display.iconify()
	#		raise e
		except Exception() as e:
			pygame.display.iconify()
			raise e

if __name__ == "__main__":
	main()
