#!/usr/bin/python
# -*- coding: utf-8 -*-

"""window draws:
projected text
menu
cursor
would be cool: scribbles
"""


import pyglet

import logger

import project
#from test_root import test_root


class Node():
	def scope():
		


def mini_test_root():
	return


class Window(pyglet.window.Window):
	def __init__(self, *args, **kwargs):
		super(Window, self).__init__(440, 400, caption='lemon party',
				resizable=True)
		self.set_icon(pyglet.image.load('icon32x32.png'))

		self.indent_spaces = 4
		self.cursor_c = self.cursor_r = 0
		self.font_width = 18
		self.font_height = 24
		self.indent_spaces = 4

#		self.root = test_root()
#		self.root.settings.fullscreen.push_handlers(on_change = self.on_settings_change)
		self.root = mini_test_root()
		self.render()

	def on_settings_change(self, setting):
		print setting
		if setting == self.root.settings.fullscreen:
			window.toggle_fullscreen()

	def render(self):
#		self.lines = project.project(self.root.render(), self.indent_spaces)
		self.lines = project.project(project.test_tags, self.indent_spaces)

	def on_resize(self, width, height):
		super(Window, self).on_resize(width, height)

	def under_cursor(self):
		return self.under_pos(self.cursor_c, self.cursor_r)

	def under_pos(self, x, y):
		return self.lines[y][x][1]["node"]

	def on_text(self, text):
		print self.under_cursor()#.dispatch_event('on_text', text)
		self.render()

	def on_text_motion(self, motion):
#		if not self.under_cursor().dispatch_event('on_text_motion', motion):
		
		if motion == pyglet.window.key.MOTION_UP:
			self.cursor_r -= 1
		if motion == pyglet.window.key.MOTION_DOWN:
			self.cursor_r += 1
		if motion == pyglet.window.key.MOTION_LEFT:
			self.cursor_c -= 1
		if motion == pyglet.window.key.MOTION_RIGHT:
			self.cursor_c += 1
			
			
			
			
		self.render()


	def on_key_press(self, key, modifiers):
		if key == pyglet.window.key.F11:
			self.toggleFullscreen()
		else:
			super(Window, self).on_key_press(key, modifiers)
			#self.on().dispatch_event('on_key_press', key, modifiers)
			#self.rerender()

	def on_mouse_press(self, x, y, button, modifiers):
		pos = self.layout.get_position_from_point(x,y)
		self.on(pos).dispatch_event('on_mouse_press', x, y, button, modifiers)
		self.rerender()




	def toggle_fullscreen(self):
		print "!fullscreen"
		self.set_fullscreen(not self.fullscreen)

	def on_draw(self):
		pyglet.gl.glClearColor(0, 0.1, 0.2, 1)
		self.clear()
		
		batch = pyglet.graphics.Batch()

		for row, line in enumerate(self.lines):
			for col, char in enumerate(line):
				pyglet.text.Label(char[0], 
					x=self.font_width * col,
					y = self.height- self.font_height * row,
					batch = batch,
					font_size = self.font_width,
					anchor_y='top'
					
					)
					
#		print "draw", self.lines
		
		pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
 			('v2i', (
 				self.font_width * self.cursor_c, 
    			self.height - self.font_height * self.cursor_r, 
    			self.font_width * self.cursor_c, 
    			self.height - self.font_height * (self.cursor_r+1))),
    		('c3B', (255,0,0,255,255,255)))
	
		


		batch.draw()


print __name__
if __name__ == "__main__":
	window = Window()
	#logger.catch(
	pyglet.app.run()
