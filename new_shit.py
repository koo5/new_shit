#!/usr/bin/python
# -*- coding: utf-8 -*-

"""window should draw:
projected text
menu
cursor
TwoDTag
wish: structured scribbles
"""

import pygame
from pygame import gfxdraw, font, image, display
import logger
import project
from test_root import test_root


def render():
	global lines
	
	tags = root.tags()
	#print tags
	lines = project.project(tags, root.indent_length, 
		root.items['settings']['projection_debug'].value)
	#print self.lines
	#self.lines = project.project(project.test_tags, self.indent_spaces)


def under_cursor(self):
	return lines[cursor_r][cursor_c][1]["node"]

"""
	def on_mouse_press(self, x, y, button, modifiers):
		pos = self.layout.get_position_from_point(x,y)
		self.on(pos).dispatch_event('on_mouse_press', x, y, button, modifiers)
		self.rerender()
"""

def toggle_fullscreen(self):
	log("!fullscreen")
	self.set_fullscreen(not self.fullscreen)

def top_keypress(event):
	global cursor_r,cursor_c

	k = event.key

	if k == pygame.K_F11:
		toggleFullscreen()
	if k == pygame.K_UP:
		cursor_r -= 1
	if k == pygame.K_DOWN:
		cursor_r += 1
	if k == pygame.K_LEFT:
		cursor_c -= 1
	if k == pygame.K_RIGHT:
		cursor_c += 1


def keypress(event):
	k = event.key

	e = active_element(cursor_c, cursor_r)
	while e != Null and not e.keypress(event):
		e = e.parent
	
	if e == Null:
		top_keypress(event)
		
	render()

def process_event(event):
	if event.type == pygame.QUIT:
		bye()
	if event.type == pygame.KEYDOWN:
		keypress(event)


def invert_color(c, max=255):
	c = list(c)
	if root.items.items['settings'].items['invert colors']:
		for i in range(len(c) / 4):
			for a in range(3):
				c[a+(4*i)] = max - c[a+(4*i)]
	return tuple(c)

def draw_root():
	for row, line in enumerate(lines):
		for col, char in enumerate(line):
			x = font_width * col
			y = font_height * row
			sur = font.render(char[0],True,invert_color(char[1]['color']),bg_color())
			screen_surface.blit(sur,(x,y))

def draw_cursor():
	gfxdraw.vline(screen_surface, 
 			font_width * cursor_c, 
    		font_height * cursor_r, 
    		font_height * cursor_r+1, 
			invert_color((255,255,255,255)))

def bg_color():
	s = root.items.items['settings'].items['background color'].items
	r = s['R'].value
	g = s['G'].value
	b = s['B'].value
	return invert_color((r,g,b))

def draw_bg():
	screen_surface.fill(bg_color())
	
def draw():
	draw_bg()
	draw_root()
	draw_cursor()
	pygame.display.flip()

def bye():
	pygame.display.iconify()
	exit()

def loop():
	process_event(pygame.event.wait())
	draw()




pygame.init()

display.set_icon(image.load('icon32x32.png'))
display.set_caption('lemon party')
screen_surface = pygame.display.set_mode((800,300), pygame.RESIZABLE)
font = font.SysFont('monospace', 24)
font_width, font_height = font.size("X")

cursor_c = cursor_r = 0

root = test_root()
root._indent_length = 4

render()

root.items['settings']['fullscreen'].push_handlers(on_change = toggle_fullscreen)




while __name__ == "__main__":
	try:
		loop()
	except KeyboardInterrupt() as e:
		pygame.display.iconify()
		raise e
	except Exception() as e:
		pygame.display.iconify()
		raise e
