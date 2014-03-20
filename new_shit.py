#!/usr/bin/python
# -*- coding: utf-8 -*-

"""window should draw:
projected text
menu
cursor
TwoDTag
wish: structured scribbles
"""

#import cProfile
import pygame, sys
from pygame import gfxdraw, font, image, display
import argparse

pygame.display.init()
pygame.font.init()

from logger import bt, log, ping
import project
import test_root
import tags as tags_module
import colors
from menu import Menu
from nodes import find_by_path
import nodes


if __debug__:
	import element as asselement
	import nodes as assnodes



parser = argparse.ArgumentParser()
parser.add_argument('--mono', action='store_true',
                   help='no colors, just black and white')
parser.add_argument('--webos', action='store_true',
                   help='webos keys hack')
args = parser.parse_args()



flags = pygame.RESIZABLE
screen_surface = None
cached_root_surface = None
lines = []


def find(x):
	return root.find(x)

def cache_colors():
	colors.cache(root.items['settings']['colors'])

def render():
	global lines, cached_root_surface
	log("render")	
	cache_colors()
	project._width = screen_surface.get_width() / font_width / 2
	project._indent_width = 4
	lines = project.project(root)
	
	if __debug__:
		assert(isinstance(lines, list))
		for l in lines:
			assert(isinstance(l, list))
			for i in l:
				#log(i)
				assert(isinstance(i, tuple))
				assert(isinstance(i[0], str) or isinstance(i[0], unicode))
				assert(len(i[0]) == 1)
				assert(isinstance(i[1], dict))
				assert(i[1]['node'])
				assert(i[1].has_key('char_index'))
			
	cached_root_surface = draw_root()
	

def by_xy((x,y)):
	c = x / font_width
	r = y / font_height
	return c,r

def under_cr((c,r)):
	try:
		return lines[r][c][1]["node"]
	except:
		return None

def under_cursor():
	return under_cr((cursor_c, cursor_r))

def element_char_index():
	try:
		return lines[cursor_r][cursor_c][1]["char_index"]
	except:
		return None

def toggle_fullscreen():
	log("!fullscreen")
	root.items['settings']['fullscreen'].value = not root.items['settings']['fullscreen'].value
	set_mode()

def set_mode():
	global screen_surface
	screen_surface = pygame.display.set_mode((1000,500), flags)# + (pygame.FULLSCREEN)) if find('settings/fullscreen/value') else 0))

def first_nonblank():
	r = 0
	for ch,a in lines[cursor_r]:
		if ch in [" ", u" "]:
			r += 1
		else:
			return r

def and_sides(event):
	if event.all[pygame.K_LEFT]: move_cursor(-1)
	if event.all[pygame.K_RIGHT]: move_cursor(1)

def and_updown(event):
	if event.all[pygame.K_UP]: updown_cursor(-1)
	if event.all[pygame.K_DOWN]: updown_cursor(1)

def top_keypress(event):
	global cursor_r,cursor_c

	k = event.key

	if k == pygame.K_F11:
		toggle_fullscreen()
	if k == pygame.K_ESCAPE:
		bye()
	if k == pygame.K_UP:
		updown_cursor(-1)
		and_sides(event)
	if k == pygame.K_DOWN:
		updown_cursor(+1)
		and_sides(event)
	if k == pygame.K_LEFT:
		move_cursor(-1)
		and_updown(event)
	if k == pygame.K_RIGHT:
		move_cursor(+1)
		and_updown(event)
	if event.mod & pygame.KMOD_CTRL:
		if k == pygame.K_LEFT:
			cursor_c -= 1
		if k == pygame.K_RIGHT:
			cursor_c += 1
	if k == pygame.K_HOME:
		if cursor_c != 0:
			cursor_c = 0
		else:
			cursor_c = first_nonblank()
	if k == pygame.K_END:
		cursor_c = len(lines[cursor_r])

class KeypressEvent(object):
	def __init__(self, e, pos, cursor):
		self.uni = e.unicode
		self.key = e.key
		self.mod = e.mod
		self.pos = pos
		self.all = pygame.key.get_pressed()
		self.cursor = cursor
		
		h = find("settings/webos hack")
		if h:
			if h.value:
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

def move_cursor(x):
	global cursor_c
	cursor_c += x

def updown_cursor(count):
	global cursor_r
	cursor_r += count


def keypress(event):
	pos = element_char_index()
	handle(KeypressEvent(event, pos, (cursor_c, cursor_r)))
		
	render()
	if under_cursor():
		menu.element = under_cursor()
		menu.items = menu.element.menu()
	else:
		menu.element = None
		menu.items = []
	draw()

def handle(e):
	if menu != None and menu.keypress(e):
		return

	element = under_cursor()
	while element != None and not element.on_keypress(e):
		element = element.parent	
	if element != None:#some element handled it
		move_cursor(root.post_render_move_caret)
		root.post_render_move_caret = 0
		return

	top_keypress(e)
	

def mousedown(e):
#	log(e.button)
	n = under_cr(by_xy(e.pos))
	if n:
		n.on_mouse_press(e.button)
		render()
		draw()


def process_event(event):
	global screen_surface
	if event.type == pygame.QUIT:
		bye()

	if event.type == pygame.KEYDOWN:
		keypress(event)

	if event.type == pygame.MOUSEBUTTONDOWN:
		mousedown(event)
		
	if event.type == pygame.VIDEORESIZE:
		log("resize")
 		screen_surface = pygame.display.set_mode(event.dict['size'],pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE)
 		render()
		draw()
 	
# 	if event.type == pygame.VIDEOEXPOSE:
#		ping()
#		draw()
 

def draw_root():
	s = pygame.Surface(screen_surface.get_size())
	s.fill(colors.bg)
	for row, line in enumerate(lines):
		for col, char in enumerate(line):
			x = font_width * col
			y = font_height * row
			sur = font.render(
				char[0],False,
				char[1]['color'],
				colors.bg)
			s.blit(sur,(x,y))
	return s

def cursor_xy():
	return (font_width * cursor_c,
			font_height * cursor_r,
			font_height * (cursor_r+1))

def draw_cursor():
	x, y, y2 = cursor_xy()
	gfxdraw.vline(screen_surface, 
			x, y, y2,    		
			colors.modify(colors.cursor))

#def draw_bg():
#	screen_surface.fill((255,0,0))#bg_color())
#	pass

def draw_menu():
	#x,_,y2 = cursor_xy()
	x, y2 = screen_surface.get_width() / 2, 0
	menu.draw(screen_surface,
		{'font':font, 'width':font_width, 'height':font_height},
		x, y2, #position
		(screen_surface.get_width() - x, screen_surface.get_height() - y2)) #size
	
	
	
def draw():
	#draw_bg()
	#draw_root()
	screen_surface.blit(cached_root_surface,(0,0))
	draw_cursor()
	draw_menu()
	pygame.display.flip()

def bye():
	log("deading")
	pygame.display.iconify()
	sys.exit()
	nodes.pyswip.prolog._original_sys_exit()	#the fuck..

def loop():
	process_event(pygame.event.wait())
	#ping()




display.set_caption('lemon party')
icon = image.load('icon32x32.png')
display.set_icon(icon)



root = test_root.test_root()
cache_colors()
menu = Menu()
cursor_c = cursor_r = 0
set_mode()


find('settings/colors/monochrome').value = args.mono



font_width = font_height = font = None
def change_font_size(setting):
	global font, font_width, font_height
	t = find('settings/font size')
	if t:
		s = t.value
	else:
		s = 8
	font = pygame.font.SysFont('monospace', s)
	font_width, font_height = font.size("X")

change_font_size(None)

#t = find('settings/fullscreen')
#if t:
#	t.push_handlers(on_change = toggle_fullscreen)

t = find('settings/font size')
if t:
	t.push_handlers(on_change = change_font_size)

t = find("settings/sdl key repeat")
if t:
	t.on_widget_edit(666)
 


#new test root here?
#https://code.google.com/p/asq/
#List should have its own menu

t = find("programs/items/0")
print t.menu()
print t.menu()[0].value
t.menu_item_selected(
	[i for i in t.menu() 
		if (isinstance(i, nodes.PlaceholderMenuItem) 
		and isinstance(i.value, nodes.Program))][0])


render()


#t = project.find(find('placeholder test/0'), lines)
#t = project.find(find('docs/4'), lines)
t = project.find(find('programs/0/statements/0'), lines)
if t:
	cursor_c, cursor_r = t

draw()



pygame.time.set_timer(pygame.USEREVENT, 100) #poll for SIGINT
def main():
	while True:
		try:
			loop()
#	except KeyboardInterrupt() as e: #add timer
#		pygame.display.iconify()
#		raise e
		except Exception() as e:
			pygame.display.iconify()
			raise e

if __name__ == "__main__":
#	cProfile.run('main')
	main()
