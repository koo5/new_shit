from __future__ import unicode_literals
from weakref import WeakValueDictionary


asselement = 666

proxied = WeakValueDictionary()


def TextTag(text):
	return text

def AttTag(k,v):
	if isinstance(v, Element): # or any nonbasic value
		idx = id(v)
		proxied[idx] = v
		return (k, idx)
	else:
		return (k,v)

def EndTag():
	return 0

def IndentTag():
	return 1

def DedentTag():
	return 2

def ArrowTag(target):
	return {"arrow": target}



def NewlineTag(Tag):
	return "\n"

def ColorTag(value):
	"""making things more uniform, this is no longer a class but a function returning an AttTag"""
	return ("color", value)



# nesting, expanded in collect()

class ChildTag(Tag):
	__slots__ = ['name']
	def __init__(self, name):
		self.name = name

class MemberTag(Tag):
	__slots__ = ['name']
	def __init__(self, name):
		self.name = name

class ElementTag(Tag):
	__slots__ = ['element']
	def __init__(self, el):
		#assert(isinstance(el, asselement.Element))
		self.element = el
