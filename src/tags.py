from lemon_utils.lemon_six import unicode



#from enum import Enum, unique
#@unique
class Att():#Enum):
	elem  = 0
	color = 1
	char_index = 2
	item_index = 3




end_tag = 0
indent_tag = 1
dedent_tag = 2
editable_start_tag = 3
editable_end_tag = 4
zwe_tag = 5 # zero width element
element_start_graphic_indicator = 6
element_end_graphic_indicator = 7



def TextTag(text):
	""" now evaluates to the text itself, used only perhaps for clarity"""
	assert isinstance(text, unicode)
	return text

def AttTag(k,v):
	"""a tuple containing an attribute"""
	return k,v

def ColorTag(value):
	"""a special case of AttTag"""
	return (Att.color, value)

def EndTag():
	"""pops an attribute"""
	return end_tag

def IndentTag():
	return indent_tag

def DedentTag():
	return dedent_tag

def ArrowTag(target, style="normal"):
	return {"arrow": target, "style":style}

def NewlineTag(Tag):
	return "\n"




# 3 variations on element/node nesting, expanded in collect()

class ChildTag():
	__slots__ = ['name']
	def __init__(self, name):
		self.name = name

class MemberTag():
	__slots__ = ['name']
	def __init__(self, name):
		self.name = name

class ElementTag():
	__slots__ = ['element']
	def __init__(self, el):
		#assert(isinstance(el, asselement.Element))
		self.element = el



