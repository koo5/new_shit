#from weakref import WeakValueDictionary
#from lemon_utils.utils import Evil

#from enum import Enum, unique

from lemon_utils.lemon_six import unicode

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
zwe_tag = 5

def TextTag(text):
	assert isinstance(text, unicode)
	return text

def AttTag(k,v):
	return k,v

def EndTag():
	return end_tag

def IndentTag():
	return indent_tag

def DedentTag():
	return dedent_tag

def ArrowTag(target):
	return {"arrow": target}

def NewlineTag(Tag):
	return "\n"

def ColorTag(value):
	return (Att.color, value)



# nesting, expanded in collect()

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
