# -*- coding: utf-8 -*-

import pyglet
from logger import log, ping
import tags



#a man needs some fun and learning
try:
	import fuzzywuzzy
	from fuzzywuzzy import process as fuzzywuzzyprocess
except:
	fuzzywuzzyprocess = None

class NotEvenAChildOrWidgetError(AttributeError):
	def __init__(self, wanted, obj):
#		super(NotEvenAChildOrWidgetError, self).__init__()
		self.obj = obj
		self.wanted = wanted
		self.message = "BANANA"
	def __str__(self):
		r = "\"%s\" is not an attribute, child or widget of %s" % (self.wanted, self.obj)
		if fuzzywuzzyprocess:
			r += ", you might have meant: " + ", ".join([i for i,v in fuzzywuzzyprocess.extractBests(self.wanted, dir(self.obj), limit=10, score_cutoff=50)]) + "..."
		return r
					

class Element(pyglet.event.EventDispatcher):
	def __init__(self):
		self.children = {}
		self.widgets = {}
	
	def __getattr__(self, name):
		if self.children.has_key(name):
			return self.children[name]
		elif self.widgets.has_key(name):
			return self.widgets[name]
		else:
			raise NotEvenAChildOrWidgetError(name, self)

	def setch(self, key, item):
		self.children[key] = item
		item.parent = self

	def setw(self, key, item):
		self.widgets[key] = item
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

	#def is_caret_on_me(self):
	#	return active == self

	#def position(self):
	#	return self.doc.positions[self]


	def tags(self):
		return [tags.NodeTag(self)] + self.render() + [tags.EndTag()]

	@property
	def win(self):
		return self.root.window

	@property
	def root(self):
		if self.parent == None:
			log("root is "+str(self))
			return self
		else:
			return self.parent.root

	def fix_relations(self):
		fix_(widgets)
		fix_(children)
	
	def fix_(self, items):
		for k,i in items.iteritems():
			i.parent = self
			i.fix_relations()	
	
	
	
