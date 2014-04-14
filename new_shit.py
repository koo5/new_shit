#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse, sys
import pygame
from pygame import gfxdraw, font, image, display

from logger import bt, log, ping
import project
import test_root
import tags as tags_module
import colors
from menu import Menu, HelpMenuItem
import nodes, element

parser = argparse.ArgumentParser()
parser.add_argument('--mono', action='store_true',
                   help='no colors, just black and white')
parser.add_argument('--webos', action='store_true',
                   help='webos keys hack')
parser.add_argument('--invert', action='store_true',
                   help='inverted colors')

args = parser.parse_args()


pygame.display.init()
pygame.font.init()


s = os.popen('xset -q  | grep "repeat delay"').read().split()
repeat_delay, repeat_rate = int(s[3]), int(s[6])
pygame.key.set_repeat(self.delay.value, 1000/self.rate.value)


flags = pygame.RESIZABLE
screen_surface = None
cached_root_surface = None
lines = []
scroll_lines = 0

def render():
	global lines, cached_root_surface
#	log("render")
	cache_colors()
	project._width = screen_surface.get_width() / font_width / 2
	project._indent_width = 4
	lines = project.project(root)[scroll_lines:]
	
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

def top_help():
	return [HelpMenuItem(t) for t in [
	"ctrl + +,- : font size",
	"up, down, left, right, home, end : move cursor",
	"f12 : normalize"
	]]

def top_keypress(event):
	global cursor_r,cursor_c
	k = event.key
	
	if pygame.KMOD_CTRL & event.mod:
		if event.uni == '+':
			find('settings/font size/widget').value += 1
			change_font_size(666)
		elif event.uni == '-':
			find('settings/font size/widget').value -= 1
			change_font_size(666)
		elif k == pygame.K_LEFT:
			cursor_c -= 1
		elif k == pygame.K_RIGHT:
			cursor_c += 1
		else:
			return False
	else:
		if k == pygame.K_F12:
			for item in root.flatten():
				if isinstance(item, nodes.Syntaxed):
					item.view_normalized = not item.view_normalized
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
		else:
			return False
	return True

class KeypressEvent(object):
	def __init__(self, e, pos, cursor):
		self.uni = e.unicode
		self.key = e.key
		self.mod = e.mod
		self.pos = pos
		self.all = pygame.key.get_pressed()
		self.cursor = cursor
		
		if settings['webos hack']:
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

def move_cursor(x):
	global cursor_c
	cursor_c += x
	if cursor_c > len(lines[cursor_r]):
		updown_cursor(1)
		cursor_c = 0

def updown_cursor(count):
	global cursor_r
	cursor_r += count


def keypress(event):
	pos = element_char_index()
	handle(KeypressEvent(event, pos, (cursor_c, cursor_r)))
		
	render()
	e = under_cursor()
	menu.element = e
	new_items = []
	while e != None:
		new_items += e.menu()
		e = e.parent
	new_items += menu.help()
	new_items += top_help()
	menu.items = new_items

	draw()

def handle(e):
	if top_keypress(e):
		return
	
	if menu != None and menu.keypress(e):
		return

	element = under_cursor()
	while element != None and not element.on_keypress(e):
		element = element.parent	
	if element != None:#some element handled it
		move_cursor(root.post_render_move_caret)
		root.post_render_move_caret = 0
		return

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




display.set_caption('lemon v 0.0 unfinished insane prototype')
icon = image.load('icon32x32.png')
display.set_icon(icon)



root = test_root.test_root()
cache_colors()
menu = Menu()
cursor_c = cursor_r = 0
set_mode()


find('settings/colors/monochrome').value = args.mono



#font_width = font_height = font = None
def change_font_size(setting=None):
	global font, font_width, font_height
	s = root['settings']['font size'].value
	font = pygame.font.SysFont('monospace', s)
	font_width, font_height = font.size("X")
root['settings']['font size'].push_handlers(on_change = change_font_size)
change_font_size()


t = find("settings/sdl key repeat")
if t:
	t.on_widget_edit(666)
 


#new test root here?
#https://code.google.com/p/asq/
#List should have its own menu

"""
t = find("programs/items/0")
print t.menu()
print t.menu()[0].value
t.menu_item_selected(
	[i for i in t.menu() 
		if (isinstance(i, nodes.PlaceholderMenuItem) 
		and isinstance(i.value, nodes.Program))][0])
"""

render()


#t = project.find(find('placeholder test/0'), lines)
#t = project.find(find('docs/4'), lines)
t = project.find(find('programs'), lines)
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
	main()
