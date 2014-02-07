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
	pass
