#!/usr/bin/python
# -*- coding: utf-8 -*-


import argparse, sys, os


import pygame
from pygame import display, image, font


from logger import bt, log, ping
import project
import tags as tags_module
import colors
from menu import Menu, InfoItem
import typed, element
import frames


element.Element.hierarchy_infoitem = InfoItem #todo:fill it somewhere





def resize(size):
	global screen_surface, screen_width, screen_height
	log("resize")
	screen_surface = pygame.display.set_mode(size, flags)
	screen_width, screen_height = screen_surface.get_size()
	resize_frames()

def resize_frames():
	root.pos = (0,0)
	root.width = screen_width / 2
	root.height = screen_height
	menu.pos = (root.width, 0)
	menu.width = screen_width / 2
	menu.height = screen_height - info.used_height
	info.pos = (root.width, menu.height)
	info.width = screen_width / 2
	info.height = info.used_height

def screen_rows():
	return screen_surface.get_height() / font_height

def cursor_xy():
	return (font_width * cursor_c,
			font_height * cursor_r,
			font_height * (cursor_r+1))

def and_sides(event):
	if event.all[pygame.K_LEFT]: move_cursor(-1)
	if event.all[pygame.K_RIGHT]: move_cursor(1)

def and_updown(event):
	if event.all[pygame.K_UP]: updown_cursor(-1)
	if event.all[pygame.K_DOWN]: updown_cursor(1)


top_help = [InfoItem(t) for t in [
	"ctrl + =,- : font size",
	"f10 : toggle brackets",
	"f9 : toggle valid-only items in menu",
	"f8 : toggle arrows",
	"f5 : eval",
	"",
	"[text] are textboxes",
	"orange <>'s denote Compiler",
	"red <>'s enclose nodes or other widgets",
	"(gray)'s are the type the compiler expects",
	" (they should go under the text box)",
	"currently you can only insert nodes manually",
	" by selecting them from the menu, with prolog,",
	" the compiler will start guessing what you mean"
	]]
	#,	"f12 : normalize syntaxes"

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
		elif k == pygame.K_LEFT:
			cursor_c -= 1
		elif k == pygame.K_RIGHT:
			cursor_c += 1
		else:
			return False
	else:
		"""if k == pygame.K_F12:
			for item in root.flatten():
				if isinstance(item, typed.Syntaxed):
					item.view_normalized = not item.view_normalized
		el"""
		if k == pygame.K_F10:
			toggle_brackets()
		elif k == pygame.K_F9:
			toggle_valid()
		elif k == pygame.K_F8:
			toggle_arrows()
		elif k == pygame.K_F5:
			run()
		elif k == pygame.K_ESCAPE:
			bye()
		elif k == pygame.K_UP:
			updown_cursor(-1)
			and_sides(event)
		elif k == pygame.K_DOWN:
			updown_cursor(+1)
			and_sides(event)
		elif k == pygame.K_LEFT:
			move_cursor(-1)
			and_updown(event)
		elif k == pygame.K_RIGHT:
			move_cursor(+1)
			and_updown(event)
		elif k == pygame.K_HOME:
			if cursor_c != 0:
				cursor_c = 0
			else:
				cursor_c = first_nonblank()
		elif k == pygame.K_END:
			cursor_c = len(lines[cursor_r])
		elif k == pygame.K_PAGEUP:
			updown_cursor(-10)
		elif k == pygame.K_PAGEDOWN:
			updown_cursor(10)

		else:
			return False
	return True

def run():
	root.root['program'].run()

def toggle_valid():
	global valid_only
	valid_only = not valid_only

def toggle_arrows():
	global arrows_visible
	arrows_visible = not arrows_visible


class KeypressEvent(object):
	def __init__(self, e, pos, cursor):
		self.uni = e.unicode
		self.key = e.key
		self.mod = e.mod
		self.pos = pos
		self.all = pygame.key.get_pressed()
		self.cursor = cursor

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
		return ("KeypressEvent(key=%s, uni=%s, mod=%s, pos=%s)" %
			(pygame.key.name(self.key), self.uni, bin(self.mod), self.pos))


def keypress(event):
	if top_keypress(e):
		return
	if menu.keypress(e):
		return
	root.keypress(e)


def mousedown(e):
#	log(e.button)
	n = under_cr(by_xy(e.pos))
	if n:
		n.on_mouse_press(e.button)
		render()

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
	screen_surface.blit(root.draw(),root.pos)
	screen_surface.blit(menu.draw(),menu.pos)
	screen_surface.blit(info.draw(),info.pos)
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
brackets = True
valid_only = False
arrows_visible = True


display.set_caption('lemon v 0.0 streamlined insane prototype with types')
icon = image.load('icon32x32.png')
display.set_icon(icon)
resize((1280,500))


change_font_size()
colors.cache(args)



root = frames.Root()
menu = frames.Menue()
info = frames.Info()




root.render()

root.cursor_c, root.cursor_r = project.find(root.root['program'].ch.statements.items[0].items[0], root.lines)
root.cursor_c += 1


update_menu()
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
