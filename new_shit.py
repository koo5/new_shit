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

flags = pygame.RESIZABLE
screen_surface = None

lines = []
cached_root_surface = None
tags=[]



def find(x):
	l = x.split("/")
	#ping()
	return find_in(root.items, l)
	
def find_in(item, path):
	#ping()
	i = tryget(item,path[0])
	if len(path) == 1 or i == None: return i
	else: return tryget(i, path[1:])

def tryget(x,y):
	#ping()
	try:
		return x.y
	except:
		try:
			return x[y]
		except:
			return None
			



def render():
	global lines,cached_root_surface,tags
	log("render")	
	#tags = ( [tags_module.ColorTag((255,255,0,255))] + project.test_tags + tags_module.EndTag()] )
	tags = root.tags()
#	print tags
	lines = project.project(tags, root.indent_length, screen_surface.get_width() / font_width)
#	print lines
	cached_root_surface = draw_root()

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
	def __init__(s, e, pos):
		s.uni = e.unicode
		s.key = e.key
		s.mod = e.mod
		s.pos = pos
	def __repr__(self):
		return ("KeypressEvent(key=%s, uni=%s, mod=%s, pos=%s)" %
			(pygame.key.name(self.key), self.uni, bin(self.mod), self.pos))

def move_cursor(x):
	global cursor_c
	cursor_c += x

def keypress(event):
	element, pos = under_cursor()
	event = KeypressEvent(event, pos)
	
	while element != None and not element.on_keypress(event):
		element = element.parent
	
	if element == None:
		top_keypress(event)
	else:	
		render()
		move_cursor(root.post_render_move_caret)
		root.post_render_move_caret = 0
	
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
 
def invert_color(c, max=255):
	if find('settings/invert colors/value'):
		print "inv ",c
		c = list(c)
		for i in range(3):
			c[i] = max - c[i]
		c = tuple(c)
	return c

def draw_root():
	s = pygame.Surface(screen_surface.get_size(),0,screen_surface)
	bg = bg_color()
	#s = screen_surface
	for row, line in enumerate(lines):
		for col, char in enumerate(line):
			x = font_width * col
			y = font_height * row
			#bt("S")
#			print char
			sur = font.render(
				char[0],False,
				invert_color(char[1]['color']),
				bg)
			s.blit(sur,(x,y))
	return s

def draw_cursor():
	gfxdraw.vline(screen_surface, 
 			font_width * cursor_c, 
    		font_height * cursor_r, 
    		font_height * (cursor_r+1), 
			invert_color((255,255,255,255)))

def bg_color():
	s = find('settings/background color/items')
	if s == None: return (0,0,100)
	r = s['R'].value
	g = s['G'].value
	b = s['B'].value
	return invert_color((r,g,b))

def draw_bg():
	screen_surface.fill((255,0,0))#bg_color())
	pass
	
def draw():
	draw_bg()
#	draw_root()
	screen_surface.blit(cached_root_surface,(0,0))
	draw_cursor()
	pygame.display.flip()

def bye():
	log("deading")
	pygame.display.iconify()
	sys.exit()

def loop():
	process_event(pygame.event.wait())
	draw()
	#ping()



pygame.init()
pygame.time.set_timer(pygame.USEREVENT, 100)

display.set_icon(image.load('icon32x32.png'))
display.set_caption('lemon party')

root = test_root.mini_test_root()
root.fix_relations()
root._indent_length = 4
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
