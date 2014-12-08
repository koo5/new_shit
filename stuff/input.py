from __future__ import unicode_literals

"""
this decorator can be used with a function that handles keypress events,
would declare the accepted keys, they could be automatically displayed
in help..

new style handler return value:
None: success
False: failure
"""
#from pygame import constants as pcs
#from pcs import KMOD_ALT, KMOD_CTRL
#known_mods = pcs.KMOD_ALT | pcs.KMOD_CTRL


"""
 other two options: decorator, but thru a metaclass. would get rid of some of the hackery. Or no decorator, and just do something like events[] = delete_self, key=xxx ...
"""

#@topic("LEvent")
def levent(**kwargs):
	"""decorator"""
	def decorator_inner_crap(function):
		function.levent_constraints = kwargs
		#log(function)
		#log(hasattr(function, "levent_constraints"))
		return function
	return decorator_inner_crap


	"""

	Element init:
		#new-style events
		#if not hasattr(self, "levent_handlers"):
		#self.__class__.levent_handlers = self.find_levent_handlers()
		#log("eee"+str(self.levent_handlers))
		#i didnt find a good way to declaratively specify key combinations
		#sometimes a mod must be, sometimes it must not be because something else
		#handles that.. i guess a handler would just have to specify which mods
		#it acccepts ..



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

	how a handler would look:
	@topic("delete_self")
	@levent(mod=KMOD_CTRL, key=K_DELETE)
	def delete_self(self):
		self.parent.delete_child(self)


	"""
