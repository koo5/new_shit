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

class NodeTag(Tag):
	"""just a special instance of AttTag, really"""
	def __init__(self, node):
		self.node = node

class ColorTag(Tag):
	def __init__(self, color):
		self.color = color

class BackspaceTag(Tag):
	def __init__(self, spaces):
		self.spaces = spaces

class TwoDGraphicTag(Tag):
	def __init__(self, width, height, draw_function):
		pass
