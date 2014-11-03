
from __future__ import print_function, unicode_literals

class dotdict(object):
	"""
	a simple object that wraps a dict and allows access by attributes.
	for example: ch = dotdict(); ch._dict = {a:1}; ch.b = ch.a + 1
	#subclassing a dict inherits many atributtes, do not want.
	#what if we used an empty object?.
	"""
	def __init__(s):#todo:, seq=None, **kwargs):
		object.__setattr__(s, "_dict", dict())
		object.__setattr__(s, "_locked", False)
	def _lock(s):
		object.__setattr__(s, "_locked", True)
	def __setattr__ (s, k, v):
		if object.__getattribute__(s, "_locked"):
			if not k in s._dict:
				raise Exception("setting an unknown item of a locked-down dotdict")

		if k != "_dict":
			s._dict[k] = v
		else:
			object.__setattr__(s, "_dict", v)

	def __getattr__ (s, k):
		return s._dict[k]
	def __setitem__(s, k, v):
		s._dict[k] = v
	def __getitem__ (s, k):
		return s._dict[k]
	def __repr__(s):
		return str(s._dict)



#https://docs.python.org/3/library/types.html#types.SimpleNamespace
#https://docs.python.org/3/library/collections.html#collections.namedtuple
