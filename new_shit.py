#!/usr/bin/python
# -*- coding: utf-8 -*-

"""window draws:
projected text
menu
cursor
would be cool: scribbles
"""


import pyglet

import project
#from test_root import test_root



class Window(pyglet.window.Window):
	def __init__(self, *args, **kwargs):
		super(Window, self).__init__(440, 400, caption='lemon party',
				resizable=True)
		self.set_icon(pyglet.image.load('icon32x32.png'))

		self.indent_spaces = 4
		self.cursor_c = self.cursor_r = 0
		self.font_size = 18
		self.indent_spaces = 4

#		self.root = test_root()
#		self.root.settings.fullscreen.push_handlers(on_change = self.on_settings_change)
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
		return self.under_pos(self.cursor_c, cursor_r)

	def under_pos(self, x, y):
		return self.lines[y][x][1]["node"]

	def on_text(self, text):
		self.under_cursor().dispatch_event('on_text', text)
		self.rerender()

	def on_text_motion(self, motion):
#		if not self.under_cursor().dispatch_event('on_text_motion', motion):
			
			
			
			
		self.rerender()


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
					x=self.font_size * col,
					y = self.height-self.font_size * row,
					batch = batch,
					font_size = self.font_size,
					anchor_y='top'
					
					)
					
		print "draw", self.lines
		batch.draw()


print __name__
if __name__ == "__main__":
	window = Window()
	pyglet.app.run()
