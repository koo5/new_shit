from lemon_utils.lemon_six import unicode
from proxy import make_proxy



#from enum import Enum, unique
#@unique
class Att():
	#these could start from zero but this is clearer
	elem  = 10
	color = 11
	char_index = 12
	item_index = 13



end_tag = 0
indent_tag = 1
dedent_tag = 2
editable_start_tag = 3
editable_end_tag = 4
zwe_tag = 5 # zero width element
element_start_graphic_indicator = 6
element_end_graphic_indicator = 7
maybe_whitespace = 8
reparse = 9



def ItemIndexTag(elem, index):
	return Att.item_index, (make_proxy(elem), index)

def ElemTag(elem):
	return Att.elem, make_proxy(elem)

def TextTag(text):
	""" now evaluates to the text itself, used only perhaps for clarity"""
	assert isinstance(text, unicode)
	return text

def AttTag(k,v):
	"""key,value"""
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
	return {"arrow": make_proxy(target), "style":style}

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



def MaybeWhitespace():
	return maybe_whitespace

def Reparse():
	return reparse
