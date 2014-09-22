# -*- coding: utf-8 -*-

from weakref import ref as weakref

import lemon_platform as platform
import event #event module from pyglet, used to pass events from widgets to parent nodes
import input #lemon's input event decorator
from logger import log, ping
import tags
from keys import *
from lemon_six import *

class Element(event.EventDispatcher):
	"""an object that can be rendered"""
	help = []
	keys = []
	keys_help_items = None
	def __init__(self):
		if platform.frontend != platform.brython: # https://github.com/PierreQuentel/brython/issues/15
			super(Element, self).__init__()
		self._parent = 666
		self.brackets_color = (200,0,0)
		self.brackets = ('<','>')
		self._render_lines = {}
		#new-style events
		#if not hasattr(self, "levent_handlers"):
		#self.__class__.levent_handlers = self.find_levent_handlers()
		#log("eee"+str(self.levent_handlers))


	#parent property wraps the weakrefing of parents
	def get_parent(s):
		#sys.getrefcount
		if type(s._parent) == weakref:
			if platform.frontend == platform.brython:
				r = s._parent.obj.obj # https://github.com/brython-dev/brython/blob/master/src/Lib/_weakref.py (?)
			else:
				r = s._parent()
			if not r: log("parent is None", s)
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


	"""
	#new-style events, only used experimentally in one place so far,
	#see input.py for the decorator that declares the event handlers
	@classmethod
	def find_levent_handlers(cls):
		r = {}
		mro = cls.mro()
		mro = reversed(mro)
		#for each class that cls is a descendant of, top to bottom:
		for c in mro:
			#log(cls)
			#iterate thru all methods and other stuff declared in that class:
			for member_name, member in c.__dict__.iteritems():
				#if member_name == "delete_self":
				#	log ("!!!" + str(member))
				#the levent decorator was here:
				if hasattr(member, "levent_constraints"):
					#log("handler found:" + str(member))
					#dicts aren't hashable, so lets convert the constraints dict
					# to a tuple and save the dict in the value
					#by "constraints" is meant the key combinations
					hash = tuple(member.levent_constraints.iteritems())
					r[hash] = (member.levent_constraints, member_name, member)
				else:
					#look if a previously found event handler function
					# is overriden in child class, this time not wrapped
					for hash,(constraints,name,function) in r.iteritems():
						if name == member_name:
							#log("updating override")
							#its overriden in a child class
							r[hash] = (constraints, name, member)
							break
		#log("returning "+str(r))
		return r

	def dispatch_levent(s, e):
		#log('dispatching '+str(e))
		for constraints, function_name, function in s.levent_handlers.itervalues():
			#log ("for constraint" + str(constraints))
			if "key" in constraints:
				if constraints['key'] != e.key:
					#log ("key doesnt match")
					continue

			if not "mod" in constraints:
				cmods = 0
			else:
				cmods = constraints['mod']

			emods = e.mod

			if cmods & KMOD_CTRL:
				if not emods & KMOD_CTRL:
					continue
			else:
				if emods & KMOD_CTRL:
					continue

			log(str(function) + 'matches')
			if function(s) != False:
				log('success')
				return True
			else:
				log('failed')
	"""


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
		help = []
		for c in s.__class__.mro():
			if c == Element:
				break #dont go further up to pyglets EventDispatcher
			if "keys" in c.__dict__:
				help += c.keys

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
	"""
	#def position(self):
	#	return self.doc.positions[self]
	

	#	def is_active(self):
	#		return False
"""

	def long__repr__(s):
		return object.__repr__(s)

	#todo
	def set_dirty(s):
		s.root.dirty = True


