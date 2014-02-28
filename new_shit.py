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

from logger import bt, log, ping
import project
import test_root
import tags as tags_module
import color
from nodes import find
from menu import Menu

if __debug__:
	import element as asselement
	import nodes as assnodes

flags = pygame.RESIZABLE
screen_surface = None
cached_root_surface = None
menu = 5
lines = []


def render():
	global lines, menu, cached_root_surface
	log("render")	
	colors.cache()
	project._width = screen_surface.get_width() / font_width
	project._indent_width = 4
	screen = project.project(root)
	lines = screen['lines']
	menu = Menu(screen['menu'])
	
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

#	print lines

def under_cursor():
	try:
		return (lines[cursor_r][cursor_c][1]["node"], lines[cursor_r][cursor_c][1]["char_index"])
	except:
		return None, None

"""
	def on_mouse_press(self, x, y, button, modifiers):
		pos = self.layout.get_position_from_point(x,y)
		self.on(pos).dispatch_event('on_mouse_press', x, y, button, modifiers)
		self.rerender()
"""

def toggle_fullscreen():
	log("!fullscreen")
	root.items['settings']['fullscreen'].value = not root.items['settings']['fullscreen'].value
	set_mode()

def set_mode():
	global screen_surface
	screen_surface = pygame.display.set_mode((800,300), flags + (pygame.FULLSCREEN if find('settings/fullscreen/value') else 0))

def top_keypress(event):
	global cursor_r,cursor_c

	k = event.key

	if k == pygame.K_F11:
		toggle_fullscreen()
	if k == pygame.K_ESCAPE:
		bye()
	if k == pygame.K_UP:
		cursor_r -= 1
	if k == pygame.K_DOWN:
		cursor_r += 1
	if k == pygame.K_LEFT:
		move_cursor(-1)
	if k == pygame.K_RIGHT:
		move_cursor(+1)
	if event.mod & pygame.KMOD_CTRL:
		if k == pygame.K_UP:
			cursor_r -= 1
		if k == pygame.K_DOWN:
			cursor_r += 1
		if k == pygame.K_LEFT:
			cursor_c -= 1
		if k == pygame.K_RIGHT:
			cursor_c += 1
	if k == pygame.K_HOME:
		cursor_c = 0
	if k == pygame.K_END:
		cursor_c = len(lines[cursor_r])

class KeypressEvent(object):
	def __init__(self, e, pos):
		self.uni = e.unicode
		self.key = e.key
		self.mod = e.mod
		self.pos = pos
	def __repr__(self):
		return ("KeypressEvent(key=%s, uni=%s, mod=%s, pos=%s)" %
			(pygame.key.name(self.key), self.uni, bin(self.mod), self.pos))

def move_cursor(x):
	global cursor_c
	cursor_c += x

def keypress(event):
	element, pos = under_cursor()

	e = KeypressEvent(event, pos)
	log(event)
	
	while element != None and not element.on_keypress(e):
		element = element.parent
	
	if element != None:#somebody handled it
		move_cursor(root.post_render_move_caret)
		root.post_render_move_caret = 0
	elif menu == None or not menu.keypress():
		top_keypress(event)
		
	render()

	
"""
def fast_render():
	global lines,cached_root_surface
	log("render")	
	tags = root.tags()
	#lines = project.project(tags, root.indent_length, root.items['settings']['projection_debug'].value)
	cached_root_surface = draw_root()
"""

def process_event(event):
	global screen_surface
	if event.type == pygame.QUIT:
		bye()
	if event.type == pygame.KEYDOWN:
		keypress(event)
		
	if event.type == pygame.VIDEORESIZE:
		log("resize")
 		screen_surface = pygame.display.set_mode(event.dict['size'],pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE)
 		render()
 	
 	if event.type == pygame.EXPOSE:
		draw()
 

def draw_root():
	s = pygame.Surface(screen_surface.get_size())
	s.fill(color.bg)
	for row, line in enumerate(lines):
		for col, char in enumerate(line):
			x = font_width * col
			y = font_height * row
			sur = font.render(
				char[0],False,
				char[1]['color'],
				color.bg)
			s.blit(sur,(x,y))
	return s

def draw_cursor():
	gfxdraw.vline(screen_surface, 
 			font_width * cursor_c, 
    		font_height * cursor_r, 
    		font_height * (cursor_r+1), 
			color.modify((255,255,255,255)))

#def draw_bg():
#	screen_surface.fill((255,0,0))#bg_color())
#	pass
	
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

def loop():
	process_event(pygame.event.wait())
	#ping()



pygame.display.init()
pygame.font.init()

pygame.time.set_timer(pygame.USEREVENT, 100)

display.set_icon(image.load('icon32x32.png'))
display.set_caption('lemon party')

root = test_root.test_root()
root.fix_relations()
cursor_c = cursor_r = 0

set_mode()

font = font.SysFont('monospace', 24)
font_width, font_height = font.size("X")

render()

if find('settings/fullscreen'):	
	find('settings/fullscreen').push_handlers(on_change = toggle_fullscreen)
#im tempted to define "it()"

if project.find(root.items['test'], lines):
	cursor_c, cursor_r = project.find(root.items['test'], lines)



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
