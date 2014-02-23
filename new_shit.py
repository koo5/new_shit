#!/usr/bin/python
# -*- coding: utf-8 -*-

"""window should draw:
projected text
menu
cursor
TwoDTag
wish: structured scribbles
"""

import pyglet
import logger
import project
from test_root import test_root





class Window(pyglet.window.Window):
	def __init__(self, *args, **kwargs):
		super(Window, self).__init__(440, 400, caption='lemon party',
				resizable=True)
		self.set_icon(pyglet.image.load('icon32x32.png'))

		self.cursor_c = self.cursor_r = 0
		self.font_width = 18
		self.font_height = 24
		self.indent_length = 4

		self.batch = pyglet.graphics.Batch()
		self.document = pyglet.text.document.FormattedDocument("")
		self.layout = pyglet.text.layout.TextLayout(
					self.document, self.width, self.height,
					multiline=True, batch=self.batch, wrap=False)
		self.layout.x = 0
		self.layout.y = 0

		self.root = test_root()
		self.root.window = self
		self.root.items['settings']['fullscreen'].push_handlers(on_change = self.on_settings_change)
		self.render()

	def on_settings_change(self, setting):
		print setting
		if setting == self.root.items.items['settings'].items['fullscreen']:
			window.toggle_fullscreen()

	def render(self):
		tags = self.root.tags()
		#print tags
		self.lines = project.project(tags, self.indent_length, self.root.items['settings']['projection_debug'].value)
		#print self.lines
#		self.lines = project.project(project.test_tags, self.indent_spaces)
		self.layout.document.text = ''.join([''.join([i[0] for i in line])  for line in self.lines])

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

	def invert(self, c, max=255):
		c = list(c)
		if self.root.items.items['settings'].items['invert colors']:
			for i in range(len(c) / 4):
				for a in range(3):
					c[a+(4*i)] = max - c[a+(4*i)]
		return tuple(c)
	#im tired. they made me do it. there was LSD in my banana.
	def on_draw(self):
		s = self.root.items.items['settings'].items['background color'].items
		r = s['R'].value
		g = s['G'].value
		b = s['B'].value
		R,G,B=self.invert((r,g,b), 255)
		pyglet.gl.glClearColor(R/255,G/255,B/255,1)
		self.clear()
		
		batch = pyglet.graphics.Batch()

		for row, line in enumerate(self.lines):
			for col, char in enumerate(line):
				#print char[0]
				pyglet.text.Label(char[0], 
					x=self.font_width * col,
					y = self.height- self.font_height * row,
					batch = batch,
					font_size = self.font_width,
					anchor_y='top'
					
					)
					
#		print "draw", self.lines
		
		#cursor
		pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
 			('v2i', (
 				self.font_width * self.cursor_c, 
    			self.height - self.font_height * self.cursor_r, 
    			self.font_width * self.cursor_c, 
    			self.height - self.font_height * (self.cursor_r+1))),
    		('c4B', self.invert((255,255,255,255,255,255,255,255))))
	
		


		batch.draw()

	def toggle_fullscreen(self):
		print "!fullscreen"
		self.set_fullscreen(not self.fullscreen)



print __name__
if __name__ == "__main__":
	window = Window()
	#logger.catch(
	pyglet.app.run()
