#!/usr/bin/python
# -*- coding: utf-8 -*-


from collections import OrderedDict
import sys
import pyglet



"""
node
astnode
dummy
widget
token
tag
"""

import events

class NotEvenAChildError(AttributeError):
	pass

class Node(events.Dispatcher):
	def __init__(self):
		self.children = {}
	
	def __getattr__(self, name):

		if self.children.has_key(name):
			return self.children[name]
		else:
			raise NotEvenAChildError(name, self)

	def set(self, key, item):
		self.children[key] = item
		item.parent = self

	def replace(self, item):
		self.parent.children[self.parent.children.values.index(self)] = item

	def on_text_input(self, text):
		print "on_text default handler:", self, text
		return False
	
	def on_cursor_motion(self, motion):
		print "on_cursor_motion default handler:", self, motion
		return False

	def on_key_press(self, symbol, modifiers):
		print "on_key_press default:", self,(
			pyglet.window.key.modifiers_string(modifiers),
			pyglet.window.key.symbol_string(symbol))
		return False
		
	def on_mouse_press(self, x, y, button, modifiers):
		print "on_mouse_press default:", self, (
			x,y,button,modifiers)
		return False

	def is_caret_on_me(self):
		return active == self

	def register_event_types(self, types):
		for item in types.split(', '):
			self.register_event_type(item)

	def position(self):
		return self.doc.positions[self]























class Window(pyglet.window.Window):
	def __init__(self, *args, **kwargs):
		super(Window, self).__init__(440, 400, caption='lemon party',
				resizable=True)
		self.set_icon(pyglet.image.load('icon32x32.png'))

		self.batch = pyglet.graphics.Batch()
		self.indentation = 0
		self.indent_length = 4
		self.register_event_type('post_render')

		self.language = language
		self.root = test_stuff()
		self.root.settings.fullscreen.push_handlers(on_change = self.on_settings_change)
		self.rerender()

	def indent(self):
		self.indentation += 1
	def dedent(self):
		self.indentation -= 1

	def squash(a):
		r = {}
		for i in a:
			r[i.items()[0][0]] = i.items()[0][1]
		return r

	def test_squash():
		if squash([{"a": 1}, {"b": 2}, {"a": 3}]) != {"a": 3, "b": 2}:
			raise Exception()

	def project(tags):
		lines = [[]]
		atts = []
		out = []
		for tag in tags:
			if isinstance(tag, AttTag):
				atts.push(tag.attribute)
			if isinstance(tag, EndTag):
				atts.pop()
            if isinstance(tag, IndentTag):
                indent+=1
            if isinstance(tag, DedentTag):
                indent-=1

			if isinstance(tag, TextTag):
				for i, letter in enumerate(tag.text):
					atts.append({"letter_index": i})
					out.append((letter, squash(atts)))
					atts.pop()
		return out
	
	def test_project():
		if str(project([AttTag({"node": 1}), TextTag("boo"), AttTag({"b":3}), TextTag("B"), EndTag(), EndTag(), TextTag("ies")])) != "[('b', {'node': 1, 'letter_index': 0}), ('o', {'node': 1, 'letter_index': 1}), ('o', {'node': 1, 'letter_index': 2}), ('B', {'node': 1, 'b': 3, 'letter_index': 0}), ('i', {'letter_index': 0}), ('e', {'letter_index': 1}), ('s', {'letter_index': 2})]":
			raise Exception()

	def break_at_newlines(self, chars):

		l = 0
		c = 0
		do_indent = True
		while c < len(chars):
			lines[l].append(chars[c])
			if chars[c] == "\n":
				lines.append([])
				l += 1
				do_indent = True
	
	screen=break_at_newlines(project(root.render)))
	for line in screen:
		for char in line;
	
		if self.do_indent:   
			self._append(self.indent_spaces(), a)
		self.do_indent = (text == "\n")
		self._append(text, a)
			
	def indent_spaces(self):
		return self.indent_length*" " * self.indentation

	def newline(self, element):
		self.append("\n", element)

	def on_settings_change(self, setting):
		print setting
		if setting == self.root.settings.fullscreen:
			window.toggle_fullscreen()

	def rerender(self):
		self.do_indent = True
		self.positions = {}
		self.active = self.on()
		self.caret_position = self.caret.position
		line = self.caret.line
		self.layout.begin_update()
		self.document.text = ""
		
		self._document = self.document
		self._caret = self.caret
		self.document = "nonono"
		self.caret = "nonono"
		
		self.root.render()
		
		self.document = self._document
		self.caret = self._caret
		
		self.document.set_style(0, len(self.document.text),
			dict(bold=False,italic=False,font_name="monospace",
			font_size=self.root.settings.font_size.value))
		self.layout.end_update()
		self.caret.line = min(line, self.layout.get_line_count()-1)
		self.dispatch_event('post_render')

	def on_resize(self, width, height):
		super(Window, self).on_resize(width, height)
		self.layout.width = self.width - 4
		self.layout.height = self.height - 4

	def _append(self, text, attributes):
		self._document.insert_text(len(self._document.text), text, attributes)
#		sys.stdout.write(text)

	
	def on(self, pos=None):
		if pos == None:
			pos = self.caret.position
#		print "pos: ",pos	
		return self.document.get_style("element", pos)
	
	def on_text(self, text):
		self.on().dispatch_event('on_text', text)
		self.rerender()

	def on_text_motion(self, motion):
		if not self.on().dispatch_event('on_text_motion', motion):
			if motion == pyglet.window.key.MOTION_PREVIOUS_PAGE:
				for i in range(0,10):
					self.caret.on_text_motion(pyglet.window.key.MOTION_UP)
			elif motion == pyglet.window.key.MOTION_NEXT_PAGE:
				for i in range(0,10):
					self.caret.on_text_motion(pyglet.window.key.MOTION_DOWN)
			else:
				print "passing to caret"
				self.caret.on_text_motion(motion)
				print self.caret.position 
				
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
		self.batch.draw()
		
		
print __name__
if __name__ == "__main__":
	window = Window()
	pyglet.app.run()
