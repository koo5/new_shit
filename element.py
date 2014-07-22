# -*- coding: utf-8 -*-

import event #event module from pyglet, used to pass events from widgets to parent nodes
import input #lemon's input event decorator
from logger import log, ping
import tags

class Element(event.EventDispatcher):
	def __init__(self):
		super(Element, self).__init__()
		self.brackets_color = (200,0,0)
		self.brackets = ('<','>')
		self._render_lines = {}
		self.levent_handlers = self.find_levent_handlers()

	def find_levent_handlers(s):
		r = {}
		for cls in type(s).mro():
			for member in cls.__dict__:
				if hasattr(member, "levent_constraints"):
					#dicts arent hashable, so lets convert the constraints dict to tuple and save the dict in value
					r[tuple(member.levent_constraints.iteritems())] = (
						member.levent_constraints, member)
		return r

	def dispatch_levent(s, e):

		for constraints, function in element.levent_handlers:
			if "key" in constraints:
				if constraints['key'] != event.key:
					continue

			if not "mod" in constraints:
				mods = 0
			else:
				mods = constraints['mod']

			if (mods & event.mod != mods) or (event.mod & input.known_mods != mod):
				continue

			#got here? the handler matches
			if function(s) != False:
				return True


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
		#this needs to be refactored in with Node.tags
		r = [tags.AttTag("node", self)] + self.render() + [tags.ColorTag(self.brackets_color), tags.TextTag(self.brackets[1]), tags.EndTag()] + [tags.EndTag()]

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
			
	def fix_parents(self):
		pass
	
	def _fix_parents(self, items):
		for i in items:
			i.parent = self
			i.fix_parents()

	def menu(self, atts):
		return []

	def hierarchy_info(self):
		r = []
		if self.__dict__.has_key("notes"):
			r += [InfoMenuItem(self.notes)]
		r += [InfoMenuItem("element: " + str(self))]
		return r

	def menu_item_selected(self, item, atts):
		if self.parent:
			return self.parent.menu_item_selected(item, atts)
	"""
	#def position(self):
	#	return self.doc.positions[self]
	

	#	def is_active(self):
	#		return False
"""
