#asselement = None

from __future__ import unicode_literals

class Tag(object):
	pass


class TextTag(Tag):
	def __init__(self, text):
		self.text = text

class AttTag(Tag):
	def __init__(self, key, val):
		self.key = key
		self.val = val


class EndTag(Tag):
	pass

class IndentTag(Tag):
	pass

class DedentTag(Tag):
	pass

class NewlineTag(Tag):
	pass


class ChildTag(Tag):
	def __init__(self, name):
		self.name = name

class WidgetTag(Tag):
	def __init__(self, name):
		self.name = name

class ElementTag(Tag):
	def __init__(self, element):
		if __debug__: # https://github.com/brython-dev/brython/issues/5
			assert(isinstance(element, asselement.Element)) #this is weird, __debug__ is true here and false there
		self.element = element

"""
class BackTabTag(Tag):
	pass
class TabTag(Tag):
	pass
"""
	
class ColorTag(Tag):
	def __init__(self, color):
		self.color = color

"""
class TwoDGraphicTag(Tag):
	def __init__(self, width, height, draw_function):
		pass

class MenuTag(Tag):
	def __init__(self, items):
		self.items = items
"""

class ArrowTag(Tag):
	def __init__(self, target):
		self.target = target
