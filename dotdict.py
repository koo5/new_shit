#optimalization: what if we replaced it with an empty object?
class dotdict(object):
	def __init__(s):#todo:, seq=None, **kwargs):
		object.__setattr__(s, "_dict", dict())
	def __setattr__ (s, k, v):
		if k == "_dict":
			object.__setattr__(s, "_dict", dict())
		else:
			s._dict[k] = v
	def __setitem__(s, k, v):
		s._dict[k] = v
	def __getattr__ (s, k):
		return s._dict[k]
	def __getitem__ (s, k):
		return s._dict[k]
	def __repr__(s):
		return str(s._dict)



