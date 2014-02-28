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
		self.element = element



class BackspaceTag(Tag):
	def __init__(self, spaces):
		self.spaces = spaces

class ColorTag(Tag):
	def __init__(self, color):
		self.color = color



class TwoDGraphicTag(Tag):
	def __init__(self, width, height, draw_function):
		pass


