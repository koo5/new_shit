# -*- coding: utf-8 -*-

import pyglet
from logger import log, ping


class NotEvenAChildError(AttributeError):
	pass

class Element(pyglet.event.EventDispatcher):
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

	def replace_with(self, item):
		self.parent.children[
				self.parent.children.values.index(self)
			] = item

	def on_text(self, text):
		ping()
		return False
	
	def on_text_motion(self, motion, select=False):
		ping()
		return False

	def on_key_press(self, symbol, modifiers):
		ping()
		return False
		
	def on_mouse_press(self, x, y, button, modifiers):
		ping()
		return False

	def register_event_types(self, types):
		for item in types.split(','):
			self.register_event_type(item.strip())

	#Что это?

	#def is_caret_on_me(self):
	#	return active == self

	#def position(self):
	#	return self.doc.positions[self]
