# -*- coding: utf-8 -*-

from menu import InfoMenuItem
import event
from logger import log, ping
import tags

class Element(event.EventDispatcher):
	def __init__(self):
		super(Element, self).__init__()
		self.brackets_color = (200,0,0)
	
	def on_keypress(self, event):
#		ping()
		return False
		
	def on_mouse_press(self, button):
		ping()
		return False

	def register_event_types(self, types):
		for item in types.split(','):
			self.register_event_type(item.strip())

	def tags(self):
		#uh
		r = self.render()
#		ping()
		assert( isinstance(r, list))
		return r
		
	@property
	def root(self):
		if self.__dict__.has_key('parent') and self.parent != None:
			return self.parent.root
		else:
			#log("root is "+str(self))
#			print self.__class__.__name__ 
			assert(self.__class__.__name__ == "Root")
			return self
			
	@property
	def indent_length(self):
		return self.parent.indent_length
			
	def fix_relations(self):
		pass
	
	def fix_(self, items):
		for i in items:
			i.parent = self
			i.fix_relations()	

	def menu(self):
		return ((self.parent.menu() if self.parent else []) +
				[InfoMenuItem("element: " + str(self))])

	def menu_item_selected(self, item):
		if self.parent:
			return self.parent.menu_item_selected(item)

	#def position(self):
	#	return self.doc.positions[self]
	

#	def is_active(self):
#		return False
