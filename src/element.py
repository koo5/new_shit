# -*- coding: utf-8 -*-

from weakref import ref as weakref

import lemon_platform as platform
import tags
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
	brackets = ('<', '>')
	def __init__(self):
		super().__init__()
		self._parent = Evil('_parent')
		self.brackets_color = colors.element_brackets

		self._render_lines = {}


	#parent property wraps the weakrefing of parents
	def get_parent(s):
		#sys.getrefcount
		if type(s._parent) == weakref:
			if platform.BRYTHON:
				r = s._parent.obj.obj # https://github.com/brython-dev/brython/blob/master/src/Lib/_weakref.py (?)
			else:
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
		s._locked = True
		#s.bananana = True

	def __setattr__(s, k, v):
		if hasattr(s, "_locked"):
			s.__getattribute__(k)#we are lockd, try if it exists
		object.__setattr__(s, k, v)


	def on_keypress(self, event):
		log('default handler')
		return False
		
	def on_mouse_press(self, button):
		log('default handler')
		return False

	def tags(elem):
		yield [AttTag(Att.elem, elem), AttTag("opening bracket", True), ColorTag(elem.brackets_color), TextTag(elem.brackets[0]), EndTag(), EndTag()]
		yield [elem.render(), ColorTag(elem.brackets_color), TextTag(elem.brackets[1]), EndTag(), EndTag()]

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



tags.Element = Element