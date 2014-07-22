#optimalization: what if we replaced it with an empty object?
class dotdict(object):
	def __init__(s):#todo:, seq=None, **kwargs):
		object.__setattr__(s, "_dict", dict())
		object.__setattr__(s, "_locked", False)
	def _lock(s):
		object.__setattr__(s, "_locked", True)
	def __setattr__ (s, k, v):
		if k == "_dict":
			object.__setattr__(s, "_dict", dict())#weird, shouldnt it set the value, not an empty dict?
		else:
			if object.__getattribute__(s, "_locked"):
				if not k in s._dict.iterkeys():
					raise Exception("setting an unknown item of a locked-down dotdict")
			s._dict[k] = v
	def __getattr__ (s, k):
		return s._dict[k]
	def __setitem__(s, k, v):
		s._dict[k] = v
	def __getitem__ (s, k):
		return s._dict[k]
	def __repr__(s):
		return str(s._dict)



