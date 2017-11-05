# -*- coding: utf-8 -*-

from weakref import ref as weakref
from types import GeneratorType


from tags import *
from lemon_utils.utils import Evil
from lemon_colors import colors


import logging


logger=logging.getLogger("root")
log=logger.debug


CHANGED = 1

class Element():
	"""an object that can be rendered, a common base for widgets and nodes"""
	help = []
	brackets = ('', '')
	def __init__(self):
		super().__init__()
		self._parent = Evil('_parent')
		self.brackets_color = colors.element_brackets

		self._render_lines = {}


	#parent property wraps the weakrefing of parents
	def get_parent(s):
		#sys.getrefcount
		if type(s._parent) == weakref:
			r = s._parent()
			if not r:
				log("%s.parent is None", s)
			return r
		else:
			return s._parent


	def set_parent(s, v):
		try:
			s._parent = weakref(v)
		except:
			s._parent = v

	parent = property(get_parent, set_parent)


	#after calling lock(), you cant set nonexisting attributes
	def lock(s):
		#s._locked = True
		#s.bananana = True
		s.__setattr__ = s.__locked__setattr__

	def __locked__setattr__(s, k, v):
		#if hasattr(s, "_locked"):
		s.__getattribute__(k)#we are lockd, try if it exists
		object.__setattr__(s, k, v)

	@property
	def module(s):
		if isinstance(s, Module):
			return s
		else:
			if s.parent != None:
				return s.parent.module
			else:
				log ("%s has no parent", s)
				assert s.__class__.__name__ == 'Root',    s
				return None

	def on_keypress(self, event):
		log('default handler')
		return False

	def on_mouse_press(self, button):
		log('default handler')
		return False

	def tags(elem):
		yield [ElemTag(elem),

				element_start_graphic_indicator,

		       AttTag("opening bracket", True), ColorTag(elem.brackets_color), elem.brackets[0], EndTag(), EndTag()]
		yield [zwe_tag, elem.render(), ColorTag(elem.brackets_color), elem.brackets[1], EndTag(),

		       element_end_graphic_indicator,

		       EndTag()]

	@property
	def root(self):
		if self.parent != None:
			return self.parent.root
		else:
			#log("root is "+str(self))
#			print self.__class__.__name__ 
			assert(self.__class__.__name__ == "Root")
			return self
			
	def fix_parents(self):
		pass
	
	def _fix_parents(self, items):
		for i in items:
			i.parent = self
			i.fix_parents()

	def menu(self, atts):
		return []

	def generate_keys_help_items(s):
		from menu_items import InfoItem
		s.keys_help_items = [InfoItem(x) for x in help]

	"""
	def create_notes_items(s):
		if self.__dict__.has_key("notes"):
			s.notes_items = [InfoItem(self.notes)]
		else:
			s.notes_items = []
	"""

	def menu_item_selected(self, item, atts):
		if self.parent:
			return self.parent.menu_item_selected(item, atts)

	def long__repr__(s):
		return object.__repr__(s)

	@property
	def ancestors(s):
		if s.parent:
			return [s.parent] + s.parent.ancestors
		else:
			return []

	def tostr(s, c=False):
		#return "".join([x for x in s.collect_tags() if isinstance(x,unicode)])
		indent = 0
		if c:
			r = s.__class__.__name__
		else:
			r = ""
		for x in s.collect_tags():
			if isinstance(x,unicode):
				for ch in x:
					r += ch
					
					if ch == "\n":
						for i in range(indent):
							r += "  "
			if x == IndentTag():
				indent += 1
			if x == DedentTag():
				indent -= 1
		return r


	def collect_tags(s):
		for t in _collect_tags(s, s.tags()):
			yield t



def _collect_tags(elem, tags):
	"""make a flat list, expanding child elements"""
	for tag in tags:
		ty = type(tag)
		#print (tag)
		if ty in (GeneratorType, list):
			#recurse
			for i in _collect_tags(elem, tag):
				yield i

		#elif ty == tuple and tag[0] == Att.elem:
		#	yield Att.elem, make_proxy(tag[1])

		#elif ty == tuple and tag[0] == Att.item_index:
		#	yield Att.item_index, (make_proxy(tag[1][0]), tag[1][1])

		elif ty == ChildTag:
			e = elem.ch[tag.name]
			for i in e.collect_tags():
				yield i

		elif ty == MemberTag:
			e = elem.__dict__[tag.name] #get the element as an attribute #i think this should be getattr, but it seems to work
			for i in e.collect_tags():
				yield i

		elif ty == ElementTag:
			e = tag.element
			for i in e.collect_tags():
				yield i

		else:
			yield tag




import tags
tags.Element = Element
