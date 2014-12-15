from weakref import WeakValueDictionary
from lemon_utils.utils import evil



proxied = WeakValueDictionary()
key_counter = 0
# distributed computing is fun.
# lets work with the theoretical possibiliy that the counter
# will overflow (makes me feel a bit easier than a runaway bignum)
# the point is that we want to be sure what object the client is talking about.
# ids can repeat. This doesnt save the clients from sending events while their data is
# outdated, but at least it cant seem they reference a different object than they mean.
#
def proxy_this(v):
	global key_counter
	while key_counter in proxied:
		key_counter += 1
	proxied[key_counter] = v
	return key_counter


node_att  = 0
color_att = 1
char_index_att = 2

def TextTag(text):
	return text

def AttTag(k,v):
	if isinstance(v, Element): # or any nonbasic value
		proxykey = proxy_this(v)
		return (k, proxykey)
	else:
		return (k,v)

end_tag = 0
def EndTag():
	return 0

indent_tag = 1
def IndentTag():
	return 1

dedent_tag = 2
def DedentTag():
	return 2

def ArrowTag(target):
	return {"arrow": proxy_this(target)}



def NewlineTag(Tag):
	return "\n"

def ColorTag(value):
	"""making things more uniform, this is no longer a class but a function returning an AttTag"""
	return ("color", value)



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
