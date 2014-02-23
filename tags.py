class Tag(object):
	pass

class TextTag(Tag):
	def __init__(self, text):
		self.text = text

class AttTag(Tag):
	def __init__(self, att):
		self.attribute = att

class EndTag(Tag):
	pass

class IndentTag(Tag):
	pass

class DedentTag(Tag):
	pass

class ChildTag(Tag):
	def __init__(self, name):
		self.name = name

class WidgetTag(Tag):
	def __init__(self, name):
		self.name = name

class BackspaceTag(Tag):
	def __init__(self, spaces):
		self.spaces = spaces

class NewlineTag(Tag):
	pass


class TwoDGraphicTag(Tag):
	def __init__(self, width, height, draw_function):
		pass

"""just a special instances of AttTag"""
class NodeTag(Tag):
	def __init__(self, node):
		self.node = node

class ColorTag(Tag):
	def __init__(self, color):
		self.color = color

