from __future__ import unicode_literals

asselement = 666


class Tag(object):
	__slots__ = []
	pass

class TextTag(Tag):
	__slots__ = ['text']
	def __init__(self, text):
		self.text = text

class AttTag(Tag):
	ID = 0
	__slots__ = ['key', 'val']
	def __init__(self, key, val):
		self.key = key
		self.val = val

class EndTag(Tag):
	ID = 1
	pass

class IndentTag(Tag):
	ID = 2
	pass

class DedentTag(Tag):
	ID = 3
	pass

class ArrowTag(Tag):
	__slots__ = ['target']
	ID = 4
	def __init__(self, target):
		self.target = target




# nesting...

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

"""
class BackTabTag(Tag):
	pass
class TabTag(Tag):
	pass
"""


class NewlineTag(Tag):
	pass

def ColorTag(value):
	"""making things more uniform, this is no longer a class but a function returning an AttTag"""
	return AttTag("color", value)

"""
class TwoDGraphicTag(Tag):
	def __init__(self, width, height, draw_function):
		pass

class MenuTag(Tag):
	def __init__(self, items):
		self.items = items
"""


