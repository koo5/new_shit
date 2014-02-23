# -*- coding: utf-8 -*-

import pyglet
from logger import log, ping
import tags

class Element(pyglet.event.EventDispatcher):
	def __init__(self):
		super(Element, self).__init__()
	
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

	def tags(self):
		#uh
		r = self.render()
		if not isinstance(r, list):
			r = [r]
		return [tags.NodeTag(self)] + r + [tags.EndTag()]

	@property
	def win(self):
		return self.root.window

	@property
	def root(self):
		if self.__dict__.has_key('parent'):
			return self.parent.root
		else:
			log("root is "+str(self))
			return self
			
	def fix_relations(self):
		self.fix_(self.widgets)
	
	def fix_(self, items):
		for k,i in items.iteritems():
			i.parent = self
			i.fix_relations()	
	

	def is_active(self):
		return False

	#def position(self):
	#	return self.doc.positions[self]
	
"""	def replace_with(self, item):
		self.parent.children[
				self.parent.children.values.index(self)
			] = item
"""
	
