#from weakref import WeakValueDictionary
#from lemon_utils.utils import Evil
from lemon_utils.lemon_six import unicode


node_att  = 0
color_att = 1
char_index_att = 2


def TextTag(text):
	assert isinstance(text, unicode)
	return text

def AttTag(k,v):
	"""
	if isinstance(v, Element): # or any nonbasic value
		proxykey = proxy_this(v)
		return (k, proxykey)
	else:"""
	return (k,v)

end_tag = 0
def EndTag():
	return end_tag

indent_tag = 1
def IndentTag():
	return indent_tag

dedent_tag = 2
def DedentTag():
	return dedent_tag

editable_start_tag = 3
editable_end_tag = 4


def ArrowTag(target):
	return {"arrow": target}

editable_end_tag = 4

def NewlineTag(Tag):
	return "\n"

def ColorTag(value):
	return (color_att, value)



# nesting, expanded in collect()

class Tag(object):
	__slots__=[]

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
