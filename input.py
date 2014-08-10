"""
this decorator can be used with a function that handles keypress events,
would declare the accepted keys, they could be automatically displayed
in help..

new style handler return value:
None: success
False: failure
"""
from logger import topic, log
from pygame import constants as pcs
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
class x(object):

	def __init__(s):
		for c in type(s).mro():
			for i in c.__dict__:
				print i
	
	@LEvent(aaa=0)
	def bbb(s):
		print "bbb"



a = x()
"""

