# -*- coding: utf-8 -*-
"""
this file defines the AST classes of the language and everything around it.
we also build up the builtins module along the way


notes on the current state of this constantly changing code:
i use kids and children interchangeably.
sometimes i use s, sometimes self.

creation of new nodes. 
__init__ usually takes children or value as arguments.
fresh() calls it with some defaults (as the user would have it inserted from the menu)
each class has a decl, which is an object descending from NodeclBase (nodecl for node declaration).
nodecl can be thought of as a type, and objects pointing to them with their decls as values of that type.
nodecls have a set of functions for instantiating the values, and those need some cleanup
and the whole language is very..umm..not well-founded...for now. improvements welcome.
"""

#from future.builtins import super #seems to break things... lets just wait to split the frontend/backend or ditch python2 pygame
from lemon_six import iteritems, iterkeys, itervalues, str_and_uni, PY2, PY3

import sys
sys.path.insert(0, 'fuzzywuzzy')
from fuzzywuzzy import fuzz

try:
	from collections import OrderedDict
except:
	from odict import OrderedDict #be compatible with older python (2.4?)

#import uni

from dotdict import dotdict
from logger import log, topic
import element
from menu_items import MenuItem
import widgets
import tags
from tags import ChildTag, ElementTag, WidgetTag, AttTag, TextTag, ColorTag, EndTag, IndentTag, DedentTag, NewlineTag, ArrowTag   #, MenuTag
from input import levent
import lemon_colors as colors
from keys import *
from utils import flatten

if __debug__:
	# asses are stuff for assertions
	import tags as asstags
	asstags.asselement = element

#for staging the builtins module and referencing builtin nodes from python code
b = OrderedDict()
building_in = True
def buildin(node, name=None):
	if building_in:
		if name == None:
			key = node
		else:
			key = name
		assert key not in b, str(key) + " already in builtins"
		b[key] = node



#crap logic, crap names, crap everything..the language is the most proof-of-conceptish i-have-no-idea-what-im-doing.
def is_decl(node):
	return isinstance(node, (NodeclBase, ParametricTypeBase))
def is_type(node):
	return is_decl(node) or isinstance(node, (Ref, Exp, Definition, SyntacticCategory, EnumType))

def make_list(btype = 'anything'):
	"make instance of List of given type"
	return  b["list"].make_type({'itemtype': Ref(b[btype])}).inst_fresh()



class Node(element.Element):
	"""a node is more than an element, its a standalone unit.
	nodes can added, cut'n'pasted around, evaluated etc.
	every node class has a corresponding decl object
	"""
	help = None
	def __init__(self):
		"""overrides in subclasses may require children as arguments"""
		super(Node, self).__init__()

		#self.color = (0,255,0,255) #i hate hardcoded colors
		self.brackets_color = "node brackets rainbow"
		self.runtime = dotdict() #various runtime data herded into one place
		self.clear_runtime_dict()
		self.isconst = False

	@property
	def brackets_color(s):
		if s._brackets_color == "node brackets rainbow":
			try:#hacky rainbow depending on the colors module
				c = colors.color("node brackets")
				hsv = tuple(colors.rgb(*c).hsv)
				hsv2 = colors.hsv((hsv[0] + 0.3*s.number_of_ancestors)%1, hsv[1], hsv[2])
				return tuple(hsv2.rgb)
			except:
				return colors.color("fg")
		return s._brackets_color

	@brackets_color.setter
	def brackets_color(s, c):
		s._brackets_color = c
	
	@property
	def number_of_ancestors(s):
		r = 0
		n = s
		try:
			while n.parent != None:
				n = n.parent
				r += 1
		except AttributeError: #crude, huh?
			pass
		return r

	def clear_runtime_dict(s):
		s.runtime._dict.clear()

	def set_parent(s, v):
		super(Node, s).set_parent(v)
		if "value" in s.runtime._dict: #messy
			s.runtime.value.parent = s.parent

	#we are overriding the parent property of Element
	parent=property(element.Element.get_parent, set_parent)

	@property
	def compiled(self):
		"all nodes except Parser return themselves"
		return self

	def scope(self):
		"""what does this node see?..poc"""
		r = []

		if isinstance(self.parent, List):
			r += [x.compiled for x in self.parent.above(self)]

		r += [self.parent]
		r += self.parent.scope()

		assert(r != None)
		assert(flatten(r) == r)
		return r

	@property
	def vardecls_in_scope(self):
		"""what variable declarations does this node see?..poc"""
		r = []

		#if isinstance(self.parent, List):
		#	above = [x.compiled for x in self.parent.above(self)]
		#	r += [i if isinstance(i, VariableDeclaration) for i in above]

		if self.parent != None:
			r += self.parent.vardecls
			r += self.parent.vardecls_in_scope

		assert(is_flat(r))
		return r

	def eval(self):
		"call _eval, save result to s.runtime"
		r = self._eval()
		assert isinstance(r, Node), str(self) + "._eval() is borked"

		#if self.isconst:
		#	self.runtime.value.set(r)
			#log("const" + str(self)) todo:figure out how const would propagate (to compiler)
		#else:
		#	self.runtime.value.append(r)
		self.append_value(r)
		return r

	def append_value(self, v):
		"store a result of evaluation or something"
		if not "value" in self.runtime._dict:
			self.runtime.value = make_list('anything')
			self.runtime.value.parent = self.parent #also has to be kept updated in the parent property setter

		self.runtime.value.append(v)
		self.runtime.evaluated = True

	def _eval(self):
		self.runtime.unimplemented = True
		return Text("not implemented")

	"""
	def program(self):
		if isinstance(self, Program):
			return self
		else:
			if self.parent != None:
				return self.parent.program()
			else:
				print self, "has no parent"
				return None
	"""

	@classmethod
	def fresh(cls):
		"make a new instance"
		return cls()

	keys = ["f7: evaluate",
		"ctrl del: delete"]
	
	def on_keypress(self, e):
		if e.key == K_F7:
			self.eval()
			return True

		if e.key == K_DELETE and e.mod & KMOD_CTRL:
			self.parent.delete_child(self)
			return True

	"""
	@topic("delete_self")
	@levent(mod=KMOD_CTRL, key=K_DELETE)
	def delete_self(self):
		self.parent.delete_child(self)
	"""

	def to_python_str(self):
		return str(self)

	@property
	def vardecls(s):
		return []

	def to_python_str(s):
		return str(s)

	def tags(self):
		elem = self
		yield AttTag("node", elem)
		for l in elem.render():
			yield l
		yield [ColorTag(elem.brackets_color), TextTag(elem.brackets[1]), EndTag()]

		#results of eval
		if "value" in elem.runtime._dict \
				and "evaluated" in elem.runtime._dict \
				and not isinstance(elem.parent, Parser): #dont show results of compiler's direct children
			yield [ColorTag('eval results'), TextTag("->")]
			v = elem.runtime.value
			if len(v.items) > 1:
				yield [TextTag(str(len(v.items))), TextTag(" values:"), ElementTag(v)]
			else:
				for i in v.items:
					yield ElementTag(i)
			yield [TextTag("<-"), EndTag()]

		yield EndTag()

	#i dont get any visitors here, nor should my code
	def flatten(self):
		r = self._flatten()
		#assert is_flat(r), (self, r)
		#return r
		return flatten(r)

	def _flatten(self):
		if not isinstance(self, (WidgetedValue, EnumVal, Ref)):
			log("warning: "+str(self)+ "flattens to self")
		return [self]

	def palette(self, scope, text, node):
		return []

	def __repr__(s):
		r = object.__repr__(s)
		try:
			r += "("+s.name+")"
		except:
			pass
		return r

	def deconstruct(s):
		return {
			'decl': s.decl
		}


class Deconstructed(Node):
	def __init__(s, data, root = None):
		if isinstance(data, dict):
			s.data = data
		elif isinstance(data, Node):
			s.data = data.deconstruct()
	def serialize(s):
		r = {}
		log("serializing Unresolved with data:", s.data)
		for k,v in iteritems(s.data):
			if isinstance(v, str_and_uni):
				r[k] = v
			elif k == "decl":
				r[k] = v.name
				log(v.name)
			else:
				r[k] = str(v)
		return r

class Unresolved(Node):
	def __init__(s, data, root = None):
		if isinstance(data, dict):
			s.data = data
		elif isinstance(data, Node):
			s.data = data.unresolvize()
#		elif
	def serialize(s):
		r = {}
		log("serializing Unresolved with data:", s.data)
		for k,v in iteritems(s.data):
			if isinstance(v, str_and_uni):
				r[k] = v
			elif k == "decl":
				r[k] = v.name
				log(v.name)
			else:
				r[k] = str(v)
		return r


def serialized2unresolved(d, r):
	new = Unresolved({})
	scope = r["builtins"].scope()
	#print scope

	#if 'decl' in d:
	#	print "looking for decl", d['decl']

	decls = [x for x in scope if is_decl(x)]

	if 'decl' in d:
		for i in decls:
			#print "this is", i.name
			if d['decl'] == i.name:
				new.data['decl'] = i
				break
	if 'text' in d:
		new.data['text'] = d['text']
	if 'target' in d:
		new.data['target'] = serialized2unresolved(d['target'], r)

	#if 'children' in d:
	#	new.data['children'] = {[(k, deserialize(v)) for k, v in d['children']]}


	return new


@topic ("serialization")
def test_serialization(r):

	#---from serialized to unresolved and back
	log("1:")
	ser = {
	'decl' : 'number',
	'text' : '4'
	}
	unr = Unresolved(i, r)
	log(out)
	ser = out.serialize()
	assert ser == i, (ser, i)

	#---
	log("2:")
	#create the range call
	c = r['program'].ch.statements[0]
	c.items.append("range")
	c.menu_item_selected([i for i in c.menu_for_item()[1:] if isinstance(i.value, FunctionCall)][0])
	log(c.compiled)

	log(c.compiled.unresolvize())
	o = Unresolved(c.compiled.unresolvize()).serialize()
	log(o)
	log(serialized2unresolved(o, r))

"""
NodeFinder?


"""

class Children(dotdict):
	pass

class Syntaxed(Node):
	"""
	Syntaxed has some named children, kept in ch.
	their types are in child_types, both are dicts
	syntax is a list of objects from module tags
	its all defined in its decl
	"""
	def __init__(self, kids):
		super(Syntaxed, self).__init__()
		self.check_slots(self.slots)
		self.syntax_index = 0
		self.ch = Children()

		assert(len(kids) == len(self.slots))

		for k in iterkeys(self.slots):
			self.set_child(k, kids[k])

		self.ch._lock()
		self.lock()

	def _serialize(s):
		return {'children': s.serialize_children()}

	def serialize_children(s):
		r = {}
		for k, v in s.ch:
			r[k] = v.serialize()
		return r

	def fix_parents(self):
		self._fix_parents(list(self.ch._dict.values()))

	def set_child(self, name, item):
		assert(isinstance(name, str))
		assert(isinstance(item, Node))
		item.parent = self
		self.ch[name] = item
		#todo:log if not Parser and not correct type

	def replace_child(self, child, new):
		"""child name or child value? thats a good question...its child the value!"""
		assert(child in itervalues(self.ch))
		assert(isinstance(new, Node))
		for k,v in iteritems(self.ch):
			if v == child:
				self.ch[k] = new
				new.parent = self
				return

		raise Exception("We should never get here")
		#todo:refactor into find_child or something

	def delete_child(self, child):
		for k,v in iteritems(self.ch._dict):
			if v == child:
				self.ch[k] = self.create_kids(self.slots)[k]
				self.ch[k].parent = self
				return

		raise Exception("We should never get here")
		#self.replace_child(child, Parser(b["text"])) #toho: create new_child()

	def _flatten(self):
		assert(isinstance(v, Node) for v in itervalues(self.ch._dict))
		return [self] + [v.flatten() for v in itervalues(self.ch._dict)]

	@staticmethod
	def check_slots(slots):
		if __debug__:
			assert(isinstance(slots, dict))
			for name, slot in iteritems(slots):
				assert(isinstance(name, str_and_uni))
				assert isinstance(slot, (NodeclBase, Exp, ParametricType, Definition, SyntacticCategory)), "these slots are fucked up:" + str(slots)


	@property
	def syntax(self):
		return self.syntaxes[self.syntax_index]

	def render(self):
		return self.syntax

	def prev_syntax(self):
		self.syntax_index  -= 1
		if self.syntax_index < 0:
			self.syntax_index = 0
		log("previous syntax")

	def next_syntax(self):
		self.syntax_index  += 1
		if self.syntax_index == len(self.syntaxes):
			self.syntax_index = len(self.syntaxes)-1
		log("next syntax")

	keys = ["ctrl ,: previous syntax",
			"ctrl .: next syntax"]
	def on_keypress(self, e):
		if KMOD_CTRL & e.mod:
			if e.key == K_COMMA:
				self.prev_syntax()
				return True
			if e.key == K_PERIOD:
				self.next_syntax()
				return True
		return super(Syntaxed, self).on_keypress(e)

	@classmethod
	def create_kids(cls, slots):
		cls.check_slots(slots)
		kids = {}
		for k, v in iteritems(slots):
			#print v # and : #todo: definition, syntaxclass. proxy is_literal(), or should that be inst_fresh?
			easily_instantiable = [b[x] for x in [y for y in ['text', 'number',
			    'statements', 'list', 'function signature list', 'untypedvar' ] if y in b]]
			#if cls == For:
			#	plog((v, easily_instantiable))
			if v in easily_instantiable:
				#log("easily instantiable:"+str(v))
				a = v.inst_fresh()
				#if v == b['statements']:
					#a.newline()#so, statements should be its own class and be defined as list of statment at the same time,
					#so the class could implement extra behavior like this?
			elif isinstance(v, ParametricType):
				a = v.inst_fresh()
			else:
				a = Parser(v)
			assert(isinstance(a, Node))
			kids[k] = a
		return kids

	@classmethod
	def fresh(cls):
		r = cls(cls.create_kids(cls.decl.instance_slots))
		return r

	@property
	def name(self):
		"""override if this doesnt work for your subclass"""
		return self.ch.name.pyval

	@property
	def syntaxes(self):
		return self.decl.instance_syntaxes

	@property
	def slots(self):
		return self.decl.instance_slots

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.ch)+"')"




class Collapsible(Node):
	"""Collapsible - List or Dict -
	they dont have a title, just a collapse button, right of which first item is rendered
	"""
	vm_collapsed = 0
	vm_oneline = 1
	vm_multiline = 2
	def __init__(self):
		super(Collapsible, self).__init__()
		self.view_mode_widget = widgets.NState(self, 0, ("+","v","-"))

	@property
	def view_mode(s):
		return s.view_mode_widget.value
	@view_mode.setter
	def view_mode(s, m):
		s.view_mode_widget.value = m

	def render(self):
		yield [WidgetTag('view_mode_widget')] + [IndentTag()]
		if self.view_mode > 0:
			if self.view_mode == 2:
				yield TextTag("\n")
			for i in self.render_items():
				yield i
		yield [DedentTag()]

	@classmethod
	#watch out: List has its own
	def fresh(cls, decl):
		r = cls()
		r.decl = decl
		return r

class Dict(Collapsible):
	def __init__(self):
		super(Dict, self).__init__()
		self.items = OrderedDict()

	def render_items(self):
		r = []
		for key, item in iteritems(self.items):
			r += [TextTag(key), TextTag(":"), IndentTag(), NewlineTag()]
			r += [ElementTag(item)]
			r += [DedentTag(), NewlineTag()]
		return r

	def __getitem__(self, i):
		return self.items[i]

	def __setitem__(self, i, v):
		self.items[i] = v
		v.parent = self

	def fix_parents(self):
		super(Dict, self).fix_parents()
		self._fix_parents(list(self.items.values()))

	def _flatten(self):
		return [self] + [v.flatten() for v in itervalues(self.items) if isinstance(v, Node)]#skip Widgets, for Settings

	def add(self, kv):
		key, val = kv
		assert(key not in self.items)
		self.items[key] = val
		assert(isinstance(key, str))
		assert(isinstance(val, element.Element))
		val.parent = self


#todo: view ordering
class List(Collapsible):
	def __init__(self):
		super(List, self).__init__()
		self.items = []

	def render_items(self):
		yield TextTag('[')
		for item in self.items:
			yield ElementTag(item)
			if self.view_mode == 2:
				yield NewlineTag()
			else:
				yield TextTag(', ')
			#we will have to work towards having this kind of syntax
			#defined declaratively so Parser can deal with it
		yield TextTag(']')


	def __getitem__(self, i):
		return self.items[i]

	def __setitem__(self, i, v):
		self.items[i] = v
		v.parent = self

	def fix_parents(self):
		super(List, self).fix_parents()
		self._fix_parents(self.items)

	keys = ["ctrl del: delete item",
			"return: add item"]
	def on_keypress(self, e):

		if e.key == K_DELETE and e.mod & KMOD_CTRL:
			item_index = self.insertion_pos(e.frame, e.cursor)
			if len(self.items) > item_index:
				del self.items[item_index]
			return True
		#???
		if e.key == K_RETURN:
			pos = self.insertion_pos(e.frame, e.cursor)
			p = Parser(self.item_type)
			p.parent = self
			self.items.insert(pos, p)
			return True

	def insertion_pos(self, frame, cl):
		(char, line) = cl
		i = -1
		for i, item in enumerate(self.items):
			if (frame in item._render_lines and
				#this will probably break finding insertion_pos and so inserting items
				#when cursor is towards the bottom of the screen
				item._render_lines[frame]["startline"] >= line and
				item._render_lines[frame]["startchar"] >= char):
				return i
		return i + 1

	def _eval(self):
		r = List()
		r.decl = self.decl
		r.items = [i.eval() for i in self.items]
		r.fix_parents()
		return r

	def copy(self):
		r = List()
		r.decl = self.decl
		r.items = [i.copy() for i in self.items]
		r.fix_parents()
		return r

	@property
	def pyval(self):
		return [i.pyval for i in self.items]
	@pyval.setter
	def pyval(self, val):
		self.items = [to_lemon(i) for i in val]
		self.fix_parents()

	def _flatten(self):
		return [self] + flatten([v.flatten() for v in self.items])

	def replace_child(self, child, new):
		assert(child in self.items)
		self.items[self.items.index(child)] = new
		new.parent = self

	def add(self, item):
		self.items.append(item)
		assert(isinstance(item, Node))
		item.parent = self

	def newline(self):
		p = Parser(self.item_type)
		p.parent = self
		self.items.append(p)

	@property
	def item_type(self):
		assert hasattr(self, "decl"), "parent="+str(self.parent)+" contents="+str(self.items)
		assert isinstance(self.decl, ParametricType), self
		return self.decl.ch.itemtype

	def above(self, item):
		assert(item in self.items)
		r = []
		for i in self.items:
			if i == item:
				return r
			else:
				r.append(i)

	def to_python_str(self):
		return "[" + ", ".join([i.to_python_str() for i in self.items]) + "]"

	@classmethod
	def fresh(cls, decl):
		r = cls()
		r.decl = decl
		"""
		try:
			r.newline()
		except NameError as e:
			pass#hack to allow calling fresh before Parser was defined
		"""
		return r

	def delete_child(s, ch):
		if ch in s.items:
			s.items.remove(ch)

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.item_type)+"')"

	@property
	def val(self):
		"""
		for "historic" reasons, when acting as a list of eval results.
		during execution, results of evaluation of every node is appended,
		so there is a history available.
		current value is the last one.
		we might split this into something like EvalResultsList
		"""
		return self[-1]

	def append(self, x):
		"""like add, but returns the item. historic reasons."""
		assert(isinstance(x, Node))
		self.items.append(x)
		x.parent = self
		return x
"""
	def set(self, x):
		#constants should call this..but if they are in a compiler, isconst wont propagate yet
		assert(isinstance(x, Node))
		if len(self) > 0:
			self[0] = x
		else:
			super(val, self).append(x)
		return x
"""

def list_of(type_name):
	"""helper to create a type"""
	return b["list"].make_type({'itemtype': Ref(b[type_name])})


class Statements(List):
	def __init__(s):
		super(Statements, s).__init__()
		s.view_mode = Collapsible.vm_multiline
	@classmethod
	def fresh(cls):
		r = cls()
		r.newline()
		return r

	@property
	def item_type(self):
		return b['statement']

	@staticmethod
	def match(text):
		return None

	def render_items(self):
		r = []
		for item in self.items:
			r += [ElementTag(item)]
			if self.view_mode == 2:
				r+= [NewlineTag()]
			else:
				r+= [TextTag(', ')]
			#we will have to work towards having this kind of syntax
			#defined declaratively so Parser can deal with it
		r += []
		return r

	def run(self):
		[i.eval() for i in self.items]
		return Text("it ran.")


class NoValue(Node):
	def __init__(self):
		super(NoValue, self).__init__()
	def render(self):
		return [TextTag('void')]
	def to_python_str(self):
		return "no value"

class Banana(Node):
	help=["runtime error. try not to throw these."]
	def __init__(self, text="error text"):
		super(Banana, self).__init__()
		self.text = text
	def render(self):
		return ["error:", TextTag(self.text)]
	def to_python_str(self):
		return "runtime error"
	@staticmethod
	def match(v):
		return False

class Bananas(Node):
	help=["parsing error. your code is bananas."]
	def __init__(self, contents=[]):
		super(Bananas, self).__init__()
		self.contents = contents
	def render(self):
		if len(self.contents) > 0:
			return [TextTag(self.to_python_str())]
		else:
			return [TextTag("?")]
	def to_python_str(self):
		return "couldnt parse " + str(len(self.contents)) + " items:"+str(self.contents)
	def _eval(s):
		return Bananas(s.contents)
	@staticmethod
	def match(v):
		return False


class WidgetedValue(Node):
	"""basic one-widget values"""
	is_const = True#this doesnt propagate to Parser yet
	def __init__(self):
		super(WidgetedValue, self).__init__()	

		#i guess its waiting for type inference

	@property
	def pyval(self):
		return self.widget.value

	@pyval.setter
	def pyval(self, val):
		self.widget.value = val

	@property
	def text(s):
		return s.widget.text

	@text.setter
	def text(s, v):
		s.widget.text = v

	def render(self):
		return [WidgetTag('widget')]

	def to_python_str(self):
		return str(self.pyval)

	def copy(s):
		return s.eval()

class Number(WidgetedValue):
	def __init__(self, value="0"):
		super(Number, self).__init__()
		self.widget = widgets.Number(self, value)
		self.widget.brackets = ('','')

	def _eval(self):
		return Number(self.pyval)

	@staticmethod
	def match(text):
		"return score"
		#log("matching "+str(text) +" with Number")
		if text.isdigit():
			#log("successs")
			return 300
		#log("nope")

class Text(WidgetedValue):

	def __init__(self, value=""):
		super(Text, self).__init__()
		self.widget = widgets.Text(self, value)
		self.brackets_color = "text brackets"
		self.brackets = ('[',']')

	def render(self):
		return self.widget.render()

	#hmm
	def on_keypress(self, e):
		return self.widget.on_keypress(e)

	def _eval(self):
		return Text(self.pyval)

	def long__repr__(s):
		return object.__repr__(s) + "('"+s.pyval+"')"

	@staticmethod
	def match(text):
		return 100



"""
class Unknown(WidgetedValue):
	will probably serve as the text bits within a Parser.
	fow now tho, it should at least be the result of explosion,

	explosion should replace a node with an Unknown for each TextTag and with its
	child nodes. its a way to try to add more text-like freedom to the structured editor.

	currently a copypasta of Text.
	def __init__(self, value=""):
		super(Unknown, self).__init__()
		self.widget = widgets.Text(self, value)
		self.brackets_color = "text brackets"
		self.brackets = ('?','?')

	def render(self):
		return self.widget.render()

	def on_keypress(self, e):
		return self.widget.on_keypress(e)

	def _eval(self):
		return Text(self.pyval)

	def long__repr__(s):
		return object.__repr__(s) + "('"+s.pyval+"')"

	@staticmethod
	def match(text):
		return 0
"""




class Root(Dict):
	def __init__(self):
		super(Root, self).__init__()
		self.parent = None
		self.post_render_move_caret = 0 #the frontend checks this.
		## The reason is for example a textbox recieves a keyboard event,
		## appends a character to its contents, and wants to move the cursor,
		## but before re-rendering, it might move it beyond end of file
		self.indent_length = 4 #not really used but would be nice to have it variable
		self.dirty = False

	def render(self):
		#there has to be some default color for everything..
		return [ColorTag("fg")] + self.render_items() + [EndTag()]

	def delete_child(self, child):
		log("I'm sorry Dave, I'm afraid I can't do that.")

	def delete_self(self):
		log("I'm sorry Dave, I'm afraid I can't do that ")


class Module(Syntaxed):
	"""module or program, really"""
	def __init__(self, kids):
		super(Module, self).__init__(kids)

	def add(self, item):
		self.ch.statements.add(item)

	def __getitem__(self, i):
		return self.ch.statements[i]

	def __setitem__(self, i, v):
		self.ch.statements[i] = v

	def scope(self):
		#crude, but for now..
		#if self != self.root["builtins"]:
		return self.root["builtins"].ch.statements.items
		#else:
		#	return [] #nothing above but Root

	def clear(self):
		st = self.ch.statements
		#print "flatten:", st.flatten()
		for i in st.flatten():
			i.clear_runtime_dict()

	def run(self):
		self.clear()
		return self.ch.statements.run()

	def run_line(self, node):
		self.clear()
		while node != None and node not in self.ch.statements.items:
			node = node.parent
		if node:
			return node.eval()







class Ref(Node):
	"""points to another node.
	if a node already has a parent, you just want to point to it, not own it"""
	#todo: separate typeref and ref?..varref..?
	def __init__(self, target):
		super(Ref, self).__init__()
		self.target = target
	def render(self):
		return [TextTag('*'), ArrowTag(self.target), TextTag(self.name)]

	@property
	def name(self):
		return self.target.name

	def works_as(self, type):
		return self.target.works_as(type)
	def inst_fresh(self):
		"""you work as a type, you have to provide this"""
		return self.target.inst_fresh()
	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.target)+"')"


class VarRef(Node):
	def __init__(self, target):
		super(VarRef, self).__init__()
		self.target = target
		assert isinstance(target, (UntypedVar, TypedArgument))
		log("varref target:"+str(target))

	def render(self):
		return [TextTag('$'), ArrowTag(self.target), TextTag(self.name)]

	@property
	def name(self):
		return self.target.name

	def _eval(s):
		return s.target.runtime.value.val

class Exp(Node):
	def __init__(self, type):
		super(Exp, self).__init__()
		self.type = type

	def render(self):
		return [WidgetTag("type"), TextTag('expr')]

	@property
	def name(self):
		return self.type.name + " expr"


class NodeclBase(Node):
	"""a base for all nodecls. Nodecls declare that some kind of nodes can be created,
	know their python class ("instance_class"), syntax and shit.
	usually does something like instance_class.decl = self, so we can instantiate the
	classes in code without going thru a corresponding nodecl.inst_fresh()"""
	help = None
	def __init__(self, instance_class):
		super(NodeclBase, self).__init__()
		self.instance_class = instance_class
		self.decl = None
		self.example = None

	#identification = ['instance_class', 'name']
	def make_example(s):
		return None

	def render(s):
		yield [TextTag(s.name), TextTag(":"), IndentTag()]

		h = None
		if s.help != None:
			h = s.help
		elif s.instance_class.help != None:
			h = s.instance_class.help
		if h != None:
			yield [TextTag("\n")] + h

		if s.example == None:
			s.example = s.make_example()
			if s.example != None:
				s.example.fix_parents()
				s.example.parent = s
		if s.example != None:
			yield [TextTag("\nexample: "), ElementTag(s.example)]

		#yield [TextTag("\nimplemented by: "+str(s.instance_class))]

		yield DedentTag()
		# t(str(self.instance_class))]

	@property
	def name(self):
		return self.instance_class.__name__.lower() #i dunno why tolower..deal with it..or change it..

	def instantiate(self, kids):
		return self.instance_class(kids)

	def inst_fresh(self):
		""" fresh creates default children"""
		return self.instance_class.fresh()

	def palette(self, scope, text, node):
			return [ParserMenuItem(self.instance_class.fresh())]

	def works_as(self, type):
		if isinstance(type, Ref):
			type = type.target
		if self == type: return True
		#todo:go thru Definitions and SyntacticCategories...this is a prolog thing

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.instance_class)+"')"

class TypeNodecl(NodeclBase):
	""" "pass me a type" kind of value
	instantiates Refs ..maybe should be TypeRefs
	"""
	help = ["points to another node, like using a previously declared identifier. Used to point to types."]
	def __init__(self):
		super(TypeNodecl, self).__init__(Ref)
		buildin(self, 'type')
		Ref.decl = self

	def palette(self, scope, text, node):
		nodecls = [x for x in scope if isinstance(x, (NodeclBase))]
		return [ParserMenuItem(Ref(x)) for x in nodecls]

	def make_example(s):
		return Ref(b['number'])

class VarRefNodecl(NodeclBase):
	help=["points to a variable"]
	def make_example(s):
		item = b['untypedvar'].instantiate({'name':Text("example variable")})
		items = list_of('text').inst_fresh()
		items.items = [Text(x) for x in ['a','b','c']]
		items.view_mode = 1
		p = FunctionCall(b['print'])
		p.args[0] = VarRef(item)
		body = b['statements'].inst_fresh()
		body.items = [p]#, Annotation(p, "this")]
		return For({'item': item,
					'items': items,
					'body': body})

	def __init__(self):
		super(VarRefNodecl, self).__init__(VarRef)
		buildin(self, 'varref')
		VarRef.decl = self
	@topic("varrefs")
	def palette(self, scope, text, node):
		r = []
		for x in node.vardecls_in_scope:
			assert isinstance(x, (UntypedVar, TypedArgument))
			r += [ParserMenuItem(VarRef(x))]
		return r
"""
	def palette(self, scope, text):
		r = []
		for x in scope:
			xc=x.compiled
			for y in x.vardecls:
				yc=y.compiled
				#log("vardecl compiles to: "+str(yc))
				if isinstance(yc, (UntypedVar, TypedArgument)):
					#log("vardecl:"+str(yc))
					r += [ParserMenuItem(VarRef(yc))]
		#log (str(scope)+"varrefs:"+str(r))
		return r
"""
class ExpNodecl(NodeclBase):
	def __init__(self):
		super(ExpNodecl, self).__init__(Exp)
		buildin(self, 'exp')
		Exp.decl = self
	def palette(self, scope, text, node):
		nodecls = [x for x in scope if isinstance(x, (NodeclBase))]
		return [ParserMenuItem(Exp(x)) for x in nodecls]

class Nodecl(NodeclBase):
	"""for simple nodes (Number, Text, Bool)"""
	def __init__(self, instance_class):
		super(Nodecl, self).__init__(instance_class)
		instance_class.decl = self
		buildin(self, self.name)
		instance_class.name = self.name

	def make_example(s):
		return s.inst_fresh()

	def palette(self, scope, text, node):
		i = self.instance_class
		m = i.match(text)
		if m:
			value = i(text)
			score = m
		else:
			value = i()
			score = 0
		return ParserMenuItem(value, score)



class SyntaxedNodecl(NodeclBase):
	"""
	child types of Syntaxed are like b["text"], they are "values",
	 children themselves are either Refs (pointing to other nodes),
	 or owned nodes (their .parent points to us)
	"""
	def __init__(self, instance_class, instance_syntaxes, instance_slots):
		super(SyntaxedNodecl , self).__init__(instance_class)
		instance_class.decl = self
		self.instance_slots = dict([(k, b[i] if isinstance(i, str) else i) for k,i in iteritems(instance_slots)])
		if isinstance(instance_syntaxes[0], list):
			self.instance_syntaxes = instance_syntaxes
		else:
			self.instance_syntaxes = [instance_syntaxes]
		buildin(self, self.instance_class.__name__.lower())
		self.example = None

	def make_example(s):
			return s.inst_fresh()



	"""
	syntaxed match(items, nodes) :-

	Text match(item, nodes) :-
		isinstance(item, Text) and item.pyval.isnum() and

	FunctionDefinition match(items, nodes
		for s, i in zip(self.sig, items)
			if isinstance(s, Text):
				if isinstance(i, Text):
					i.pyval
	"""

class ParametricTypeBase(Syntaxed):
	pass

class ParametricType(ParametricTypeBase):
	"""like..list of <type>, the <type> will be a child of this node.
	 ParametricType is instantiated by ParametricNodecl"""
	def __init__(self, kids, decl):
		self.decl = decl
		super(ParametricType, self).__init__(kids)
		#self.lock()

	@property
	def slots(self):
		return self.decl.type_slots

	@property
	def syntaxes(self):
		return [self.decl.type_syntax]

	def inst_fresh(self):
		"""create new List or Dict"""
		return self.decl.instance_class.fresh(self)

	@classmethod
	def fresh(cls, decl):
		"""create new parametric type"""
		return cls(cls.create_kids(decl.type_slots), decl)

	@property
	def name(self):
		return "parametric type (probably list)"
		#todo: refsyntax?
	#@property
	#def refsyntax(s):
	#damn this is just all wrong. name should return something like "list of numbers"
	#should i expose a wrapper for project that would return a string?
	#or do we want to display the name as a node?
	#you cant render a different nodes syntax as your own
	#make a new kind of tag for this?

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.ch)+"')"



class ParametricNodecl(NodeclBase):
	"""says that "list of <type>" declaration could exist, instantiates it (ParametricType)
	only non Syntaxed types are parametric now(list and dict),
	so this contains the type instance's syntax and slots (a bit confusing)"""
	def __init__(self, instance_class, type_syntax, type_slots):
		super(ParametricNodecl, self).__init__(instance_class)
		self.type_slots = type_slots
		self.type_syntax = type_syntax

	def make_type(self, kids):
		return ParametricType(kids, self)

	def palette(self, scope, text, node):
		return [ParserMenuItem(ParametricType.fresh(self))]
	#def obvious_fresh(self):
	#if there is only one possible node type to instantiate..





class EnumVal(Node):
	def __init__(self, decl, value):
		super(EnumVal, self).__init__()
		self.decl = decl
		self.value = value

	@property
	def pyval(self):
		return self.value

	@pyval.setter
	def pyval(self, val):
		self.value = val

	def render(self):
		return [TextTag(self.to_python_str())]

	def to_python_str(self):
		text = self.decl.ch.options[self.value].compiled
		assert isinstance(text, Text), text
		return text.pyval

	def copy(s):
		return s.eval()

	def _eval(self):
		return EnumVal(self.decl, self.value)

	#@staticmethod
	#def match(text):
	#	"return score"
	#	if text.isdigit():
	#		return 300


class EnumType(ParametricTypeBase):
	"""works as a type but doesnt descend from Nodecl. Im just trying stuff..."""
	def __init__(self, kids):
		self.instance_class = EnumVal
		super(EnumType, self).__init__(kids)
	def palette(self, scope, text, node):
		r = [ParserMenuItem(EnumVal(self, i)) for i in range(len(self.ch.options.items))]
		#print ">",r
		return r
	def works_as(self, type):
		if isinstance(type, Ref):
			type = type.target
		if self == type: return True
	def inst_fresh(s):
		return EnumVal(s, 0)

"""here we start putting stuff into b, which is then made into the builtins module"""
b[0] = Text(
"""We start by declaring the existence of some types.
Once declared, we can reference them from lemon code.
Internally, each declaration is a Nodecl object. The type name is always a lowercased
name of the python class that implements the type.""")

TypeNodecl() #..so you can say that your function returns a type value, or something
VarRefNodecl()

[Nodecl(x) for x in [Number, Text, Statements, Banana, Bananas]]

"""the stuff down here isnt well thought-out yet..the whole types thing.."""

class SyntacticCategory(Syntaxed):
	help=['this is a syntactical category(?) of nodes, used for "statement" and "expression"']

	def __init__(self, kids):
		super(SyntacticCategory, self).__init__(kids)
		buildin(self, self.ch.name.pyval)


class WorksAs(Syntaxed):
	help=["declares a subtype relation between two existing types"]
	def __init__(self, kids):
		super(WorksAs, self).__init__(kids)
		buildin(self)
	@classmethod
	def b(cls, sub, sup):
		cls({'sub': Ref(b[sub]), 'sup': Ref(b[sup])})

class Definition(Syntaxed):
	"""should have type functionality (work as a type)"""
	help=['used just for types, currently.']
	def __init__(self, kids):
		super(Definition, self).__init__(kids)
		buildin(self, self.ch.name.pyval)

	def inst_fresh(self):
		return self.ch.type.inst_fresh()

	def palette(self, scope, text, node):
		return self.ch.type.palette(scope, text, None)


class Union(Syntaxed):
	help=['an union of types means that any type will satisfy']
	def __init__(self, children):
		super(Union, self).__init__(children)

SyntaxedNodecl(SyntacticCategory,
			   [TextTag("syntactic category:"), ChildTag("name")],
			   {'name': 'text'})
SyntaxedNodecl(WorksAs,
			   [ChildTag("sub"), TextTag("works as"), ChildTag("sup")],
			   {'sub': 'type', 'sup': 'type'})
SyntaxedNodecl(Definition,
			   [TextTag("define"), ChildTag("name"), TextTag("as"), ChildTag("type")], #expression?
			   {'name': 'text', 'type': 'type'})

SyntacticCategory({'name': Text("anything")})
SyntacticCategory({'name': Text("statement")})
SyntacticCategory({'name': Text("expression")})
WorksAs.b("statement", "anything")
WorksAs.b("expression", "statement")
WorksAs.b("number", "expression")
WorksAs.b("text", "expression")

buildin(ParametricNodecl(List,
				 [TextTag("list of"), ChildTag("itemtype")],
				 {'itemtype': b['type']}), 'list')
buildin(ParametricNodecl(Dict,
				 [TextTag("dict from"), ChildTag("keytype"), TextTag("to"), ChildTag("valtype")],
				 {'keytype': b['type'], 'valtype': Exp(b['type'])}), 'dict')

WorksAs.b("list", "expression")
WorksAs.b("dict", "expression")

class ListOfAnything(ParametricType):
	@topic ("ListOfAnything palette")
	def palette(self, scope, text, node):
		#log(self.ch._dict)
		i = self.inst_fresh()
		i.view_mode = 1
		i.newline()
		return [ParserMenuItem(i)]
	def works_as(self, type):
		return True

buildin(ListOfAnything({'itemtype':b['anything']}, b['list']), 'list of anything')

SyntaxedNodecl(EnumType,
			   ["enum", ChildTag("name"), ", options:", ChildTag("options")],
			   {'name': 'text',
			   'options': list_of('text')})

#Definition({'name': Text("bool"), 'type': EnumType({
#	'name': Text("bool"),
#	'options':b['enumtype'].instance_slots["options"].inst_fresh()})})
buildin(EnumType({'name': Text("bool"),
	'options':b['enumtype'].instance_slots["options"].inst_fresh()}), 'bool')

b['bool'].ch.options.items = [Text('false'), Text('true')]
buildin(Text("for use from within python:"))
b['false'] = EnumVal(b['bool'], 0)
b['true'] = EnumVal(b['bool'], 1)

#Definition({'name': Text("statements"), 'type': b['list'].make_type({'itemtype': Ref(b['statement'])})})

SyntaxedNodecl(Module,
			   ["module:\n", ChildTag("statements"),  TextTag("end.")],
			   {'statements': b['statements']})

Definition({'name': Text("list of types"), 'type': b['list'].make_type({'itemtype': Ref(b['type'])})})

SyntaxedNodecl(Union,
			   [TextTag("union of"), ChildTag("items")],
			   {'items': b['list'].make_type({'itemtype': b['type']})}) #todo:should work with the definition from above instead
b['union'].notes="""should appear as "type or type or type", but a Syntaxed with a list is an easier implementation for now"""




class UntypedVar(Syntaxed):
	def __init__(self, kids):
		super(UntypedVar, self).__init__(kids)

SyntaxedNodecl(UntypedVar,
			   [ChildTag("name")],
			   {'name': 'text'})

class For(Syntaxed):
	def __init__(self, children):
		super(For, self).__init__(children)

	@property
	def vardecls(s):
		return [s.ch.item]

	def _eval(s):
		itemvar = s.ch.item.compiled
		if not isinstance(itemvar, UntypedVar):
			return Banana('itemvar isnt UntypedVar')
		items = s.ch.items.eval()
		if not isinstance(items, List):
			return Banana('items isnt List')
		#r = b['list'].make_type({'itemtype': Ref(b['statement'])}).make_inst() #just a list of the "anything" type..dunno
		for item in items:
			itemvar.append_value(item)
			s.ch.body.run()

		return NoValue()

SyntaxedNodecl(For,
			   [TextTag("for"), ChildTag("item"), ("in"), ChildTag("items"),
			        ":\n", ChildTag("body")],
			   {'item': b['untypedvar'],
			    'items': Exp(
				    b['list'].make_type({
				        'itemtype': Ref(b['type'])#?
				    })),
			   'body': b['statements']})

class VarlessFor(Syntaxed):
	def __init__(self, children):
		self.it = b['untypedvar'].inst_fresh()
		self.it.ch.name.pyval = "it"
		super(VarlessFor, self).__init__(children)

	@property
	def vardecls(s):
		return [s.it]

	def _eval(s):
		items = s.ch.items.eval()
		assert isinstance(items, List), items
		for item in items:
			s.it.append_value(item)
			s.ch.body.run()
		return NoValue()

SyntaxedNodecl(VarlessFor,
			   [TextTag("for"), ChildTag("items"),
			        ":\n", ChildTag("body")],
			   {'items': Exp(list_of('type')),
			   'body': b['statements']})


class If(Syntaxed):
	def __init__(self, children):
		super(If, self).__init__(children)

	def _eval(s):
		c = s.ch.condition.eval()
		#lets just do it by hand here..
		if c.decl == b['bool'] and c.pyval == 1:
			s.ch.statements.run()

		return NoValue()

SyntaxedNodecl(If,
			[
				[TextTag("if"), ChildTag("condition"), ":\n", ChildTag("statements")],

			],
			{'condition': Exp(b['bool']),
			'statements': b['statements']})

"""...notes: formatting: we can speculate that we will get to having a multiline compiler,
and that will allow for a more freestyle formatting...
"""



"""
class Filter(Syntaxed):
	def __init__(self, kids):
		super(Filter, self).__init__(kids)
"""




"""
Parser node

todo:hack it so that the first node, when a second node is added, is set as the
leftmost child of the second node..or maybe not..dunno
"""


class ParserBase(Node):
	def __init__(self):
		super(ParserBase, self).__init__()
		self.items = []
		self.decl = None
		self.register_event_types('on_edit')
		self.brackets_color = "compiler brackets"
		self.brackets = ('{', '}')

	def __getitem__(self, i):
		return self.items[i]

	@property
	def nodes(s):
		return [i for i in s.items if isinstance(i, Node) ]

	def fix_parents(self):
		super(ParserBase, self).fix_parents()
		self._fix_parents(self.nodes)

	def _flatten(self):
		return [self] + flatten([v.flatten() for v in self.items if isinstance(v, Node)])

	def add(self, item):
		self.items.append(item)
		assert(isinstance(item, Node))
		item.parent = self

	def edit_text(s, ii, pos, e):
		#item index, cursor position in item, event
		text = s.items[ii]
		if e.key == K_BACKSPACE:
			if pos > 0 and len(text) > 0 and pos <= len(text):
				text = text[0:pos -1] + text[pos:]
				s.root.post_render_move_caret -= 1
		else:
			assert isinstance(text, str_and_uni), (s.items, ii, text)
			#print "assert(isinstance(text, (str, unicode)), ", s.items, ii, text
			text = text[:pos] + e.uni + text[pos:]
			s.root.post_render_move_caret += len(e.uni)

		s.items[ii] = text

		#log(self.text + "len: " + len(self.text))
		s.dispatch_event('on_edit', s)
		return True


		"""
				if e.key == K_BACKSPACE:
					if pos > 0 and len(self.text) > 0 and pos <= len(self.text):
						self.text = self.text[0:pos -1] + self.text[pos:]
		#				log(self.text)
						self.root.post_render_move_caret = -1
				if e.key == K_DELETE:
					if pos >= 0 and len(self.text) > 0 and pos < len(self.text):
						self.text = self.text[0:pos] + self.text[pos + 1:]
		"""

	def render(self):
		if len(self.items) == 0: #hint at the type expected
			return self.empty_render()

		r = [AttTag("compiler body", self)]
		for i, item in enumerate(self.items):
			r += [AttTag("compiler item", i)]
			if isinstance(item, str_and_uni):
				for j, c in enumerate(item):
					r += [AttTag("compiler item char", j), TextTag(c), EndTag()]
			else:
				r += [ElementTag(item)]
			r += [EndTag()]
		r += [EndTag()]
		return r

	keys = ["text editing",
			"ctrl del: delete item"]
	"""
	def on_keypress(s, e):

		if not e.mod & KMOD_CTRL:
			assert s.root.post_render_move_caret == 0

			if e.uni and e.key not in [K_ESCAPE, K_RETURN]:

				items = s.items
				atts = e.atts

				if len(items) != 0:
					#it's Parser's closing bracket
					if not "compiler body" in atts or s != atts["compiler body"]:
						if isinstance(items[-1], Node): #is my last item a node?
							items.append("")
						#in either case
						return s.edit_text(len(items) - 1, len(items[-1]), e)
					else:
						ci = atts["compiler item"]
						if "opening bracket" in atts:
							if ci == 0 or isinstance(items[ci-1], Node):
								items.insert(ci, "")
								return s.edit_text(ci,0,e)
							else:
								return s.edit_text(ci - 1, len(items[ci-1]), e)
						else:
							if isinstance(items[ci], Node):
								#its an event passed up from a child
								return False
							else:
								#we are in the middle of text
								return s.edit_text(ci, atts["compiler item char"], e)
					#there is never a closing bracket, the child handles it
				else: # no items in me
					s.items.append("")
					#snap cursor to the beginning of Parser
					s.root.post_render_move_caret -= atts['char_index']
					return s.edit_text(0, 0, e)

		return super(Parser, s).on_keypress(e)
	"""
	"""
	@topic ("type tree")
	def type_tree(s, type, scope, indent=0):
		log(" "*indent, type)
		for i in scope:
			if is_decl(i):
				for j in scope:
					if isinstance(j, WorksAs):
						if j.ch.sup == i:
							type_tree(i, scope, indent+1)


				s.type_tree(i, scope, indent + 1)
	"""
	def on_keypress(s, e):

		if e.mod & KMOD_CTRL:
			if e.key == K_t:
				s.type_tree(s.type, s.scope())
				return True
			else:
				return super(ParserBase, s).on_keypress(e)

		if e.key == K_ESCAPE:
			return False
		if e.key == K_RETURN:
			return False
		if (not e.uni) and not e.key in [K_BACKSPACE]: #backspace and something else comes with some unicode
			return False

		assert s.root.post_render_move_caret == 0

		items = s.items
		atts = e.atts
		i = s.mine(atts)

		if i == None:
			items.append("")
			#snap cursor to the beginning of Parser
			s.root.post_render_move_caret -= atts['char_index']
			return s.edit_text(0, 0, e)
		elif isinstance(items[i], str_and_uni):
			if "compiler item char" in atts:
				ch = atts["compiler item char"]
			else:
				ch = len(items[i])
			return s.edit_text(i, ch, e)
		elif isinstance(items[i], Node):
			items.insert(i, "")
			assert isinstance(items[i], str_and_uni), (items, i)
			return s.edit_text(i, 0, e)

	def mine(s, atts):
		"""
		atts are the attributs of the char under cursor,
		passed to us with an event. figure out if and which of our items
		is there
		this is an abstraction of the logic above i guess...
		"""

		if len(s.items) != 0:
			if not "compiler body" in atts or s != atts["compiler body"]:
				#we should only get an event if cursor is on us, so this
				#only can be our closing bracket
				return len(s.items)-1 #first from end
			else:
				ci = atts["compiler item"]
				if "opening bracket" in atts:
					if ci == 0:
						return 0
					else:
						return ci - 1
				else:
					return ci
		else: # no items in me
			return None


	"""
	def mine(self, atts):
		#doesnt this need changes after the rewrite?
		if "compiler body" in atts and self == atts["compiler body"]:
			#if "compiler item" in atts and atts["compiler item"] in self.items:
			return atts["compiler item"]
		elif len(self.items) != 0 and atts["node"] == self:
			#cursor is on the closing bracket of Parser
			return len(self.items) - 1
		#else None
	"""

	def menu_item_selected(s, item, atts=None):
		if atts == None:
			i = 0
		else:
			i = s.mine(atts)
		return s.menu_item_selected_for_child(item, i)

	@staticmethod
	def first_child(node):
		for i in node.syntax:
			if isinstance(i, ChildTag):
				return node.ch[i.name]
		return node

	def post_insert_move_cursor(s, node):
		#move cursor to first child or somewhere sensible. this should go somewhere else.
		if isinstance(node, Syntaxed):
			fch = s.first_child(node)
			if isinstance(fch, Syntaxed):
				fch = s.first_child(fch)
			s.root.post_render_move_caret = fch
		elif isinstance(node, FunctionCall):
			if len(node.args) > 0:
				s.root.post_render_move_caret = node.args[0]
		elif isinstance(node, WidgetedValue):
			if len(node.widget.text) > 0:
				s.root.post_render_move_caret += 2
				#another hacky option: post_render_move_caret_after
				#nonhacky option: render out a tag acting as an anchor to move the cursor to
				#this would be also useful above
		elif isinstance(node, List):
			if len(node.items) > 0:
				s.root.post_render_move_caret = node.items[0]
		#todo etc. make the cursor move naturally

	def menu(self, atts, debug = False):
		return self.menu_for_item(self.mine(atts), debug)

	def delete_child(s, child):
		log("del")
		del s.items[s.items.index(child)]



class Parser(ParserBase):
	"""the awkward input node AKA the Beast.
	im thinking about rewriting the items into nodes again.
	 this time with smarter cursor movement.
	"""
	def __init__(self, type):
		super(Parser, self).__init__()
		assert is_type(type), str(type)
		self.type = type

	def empty_render(s):
		return [ColorTag("compiler hint"), TextTag('('+s.type.name+')'), EndTag()]

	@property
	def compiled(self):
		#default result:		#raise an exception?
		r = Bananas(self.items)

		if len(self.items) == 1:
			i0 = self.items[0]
			if isinstance(i0, Node):
				r = i0
			else: #string
				#demodemodemo
				type = self.type
				if isinstance(self.type, Exp):
					type = self.type.type
				if isinstance(type, Ref):
					type = type.target

#				if type == b['number']:
				if Number.match(i0):
					r = Number(i0)
						#log("parsed it to Number")

				if type == b['text']:
					r = Text(i0)


		r.parent = self
		#log(self.items, "=>", r)
		return r

	def _eval(self):
		return self.compiled.eval()

	"""
	def replace_child(self, child, new):
		assert(child in self.items)
		self.items[self.items.index(child)] = new
		new.parent = self
		#add a blank at the end
		p = SomethingNew()
		p.parent = self
		self.items.append(p)
	"""
	"""
	def eval(self):
		i = self.items[0]
		i.eval()
		self.runtime = i.runtime
		return self.runtime.value.val
	"""

	#todo: make previous item the first child of the inserted item if applicable
	def menu_item_selected_for_child(self, item, child_index):
		assert isinstance(item, (ParserMenuItem, DefaultParserMenuItem))
		if isinstance(item, ParserMenuItem):
			node = item.value
			if child_index != None:
				self.items[child_index] = node
			else:#?
				self.items.append(node)
			node.parent = self
			self.post_insert_move_cursor(node)
			return True
		elif isinstance(item, DefaultParserMenuItem):
			return False
		else:
			raise Exception("whats that shit, cowboy?")

	@topic("menu")
	def menu_for_item(self, i=0, debug = False):

		if i == None:
			if len(self.items) == 0:
				text = ""
			else:
				return []
		else:
			if isinstance(self.items[i], Node):
				text = ""
			else:
				text = self.items[i]

		scope = self.scope()
		menu = flatten([x.palette(scope, text, self) for x in scope])

		#slot type is Nodecl or Definition or AbstractType or ParametrizedType
		#first lets search for things in scope that are already of that type
		#for i in menu:
		#	if i.value.decl.eq(type):
		#		v.score += 1

		type = self.type
		if isinstance(type, Exp):
			type = type.type
			exp = True
		else:
			exp = False

		matchf = fuzz.token_set_ratio#partial_ratio

		for item in menu:
			v = item.value
			try:
				item.scores.name = matchf(v.name, text), v.name #0-100
			except Exception as e:
				#print e
				pass

			item.scores.declname = 3*matchf(v.decl.name, text), v.decl.name #0-100


			if item.value.decl.works_as(type):
				item.scores.worksas = 200
			else:
				item.invalid = True

			#search thru syntaxes
			#if isinstance(v, Syntaxed):
			#	for i in v.syntax:
			#   		if isinstance(i, t):
			#			item.score += fuzz.partial_ratio(i.text, self.pyval)
			#search thru an actual rendering(including children)
			tags =     v.render()
			texts = [i.text for i in tags if isinstance(i, TextTag)]
			#print texts
			texttags = " ".join(texts)
			item.scores.texttags = matchf(texttags, text), texttags


		menu.sort(key=lambda i: i.score)

		if debug:
			print ('MENU FOR:',text,"type:",self.type)
			[log(str(i.value.__class__.__name__) + str(i.scores._dict)) for i in menu]

		menu.append(DefaultParserMenuItem(text))
		menu.reverse()#umm...

		return menu

	def long__repr__(s):
		return object.__repr__(s) + "(for type '"+str(s.type)+"')"


class LeshCommandLine(ParserBase):
	def __init__(self):
		super(LeshCommandLine, self).__init__()

	def empty_render(s):
		return []

	def menu_item_selected_for_child(self, item, child_index, alt=False):
		assert isinstance(item, (LeshMenuItem, DefaultParserMenuItem))
		if isinstance(item, LeshMenuItem):

			dec = item.value

			if alt:
				snippet = LeshSnippet(dec)
			else:
				snippet = dec.command

			if child_index != None:
				#if isinstance(self.items[child_index], str_or_uni):
					#todo:split at pipes

				self.items[child_index] = snippet
			else:
				self.items.append(snippet)

			if alt:
				snippet.parent = self
			#self.post_insert_move_cursor(node)
			return True

		elif isinstance(item, DefaultParserMenuItem):
			return False
		else:
			raise Exception("whats that shit, cowboy?")

	@topic("lesh menu")
	def menu_for_item(self, i=0, debug = False):

		if i == None:
			if len(self.items) == 0:
				text = ""
			else:
				return []
		else:
			if isinstance(self.items[i], Node):
				text = ""
			else:
				text = self.items[i]

		scope = b
		menu = flatten([x.palette(scope, text, self) for x in scope if isinstance(x, LeshSnippetDeclaration)])

		matchf = fuzz.token_set_ratio#partial_ratio

		for item in menu:
			v = item.value
			item.scores.human = matchf(v.human, text), v.human #0-100
			item.scores.command = matchf(v.command, text), v.command#0-100

		menu.sort(key=lambda i: i.score)

		menu.append(DefaultParserMenuItem(text))
		menu.reverse()

		return menu


class ParserMenuItem(MenuItem):
	def __init__(self, value, score = 0):
		super(ParserMenuItem, self).__init__()
		self.value = value
		value.parent = self
		self.scores = dotdict()
		self.brackets_color = (0,255,255)

	@property
	def score(s):
		#print s.scores._dict
		return sum([i if not isinstance(i, tuple) else i[0] for i in itervalues(s.scores._dict)])

	def tags(self):
		return [WidgetTag('value'), ColorTag("menu item extra info"), " - "+str(self.value.__class__.__name__)+' ('+str(self.score)+')', EndTag()]

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.value)+"')"

class LeshMenuItem(MenuItem):
	#hack
	def __init__(self, snippet, score = 0):
		super(LeshMenuItem, self).__init__()
		self.value = snippet
		self.scores = dotdict()
		self.brackets_color = (0,255,255)

	@property #duplicate...
	def score(s):
		return sum([i if not isinstance(i, tuple) else i[0] for i in itervalues(s.scores._dict)])

	def tags(self):
		return [self.value.human, ":\n", self.value.command]


class DefaultParserMenuItem(MenuItem):
	def __init__(self, text):
		super(DefaultParserMenuItem, self).__init__()
		self.text = text
		self.brackets_color = (0,0,255)

	def tags(self):
		return [TextTag(self.text)]





"""

functions

"""

#todo function arguments:#mode = eval/pass, untyped argument,
#todo optional function return type
#todo: show and hide argument names. syntaxed?

class TypedArgument(Syntaxed):
	def __init__(self, kids):
		super(TypedArgument, self).__init__(kids)

SyntaxedNodecl(TypedArgument,
			   [ChildTag("name"), TextTag("-"), ChildTag("type")],
			   {'name': 'text', 'type': 'type'})

class UnevaluatedArgument(Syntaxed):
	def __init__(self, kids):
		super(UnevaluatedArgument, self).__init__(kids)

SyntaxedNodecl(UnevaluatedArgument,
			   [TextTag("unevaluated"), ChildTag("argument")],
			   {'argument': 'typedargument'})



tmp = b['union'].inst_fresh()
tmp.ch["items"].add(Ref(b['text']))
tmp.ch["items"].add(Ref(b['typedargument']))
tmp.ch["items"].add(Ref(b['unevaluatedargument']))
Definition({'name': Text('function signature node'), 'type': tmp})

tmp = b['list'].make_type({'itemtype': Ref(b['function signature node'])})
Definition({'name': Text('function signature list'), 'type':tmp})




class FunctionDefinitionBase(Syntaxed):

	def __init__(self, kids):
		super(FunctionDefinitionBase, self).__init__(kids)

	@property
	def args(self):
		return [i for i in self.sig if isinstance(i, (TypedArgument, UnevaluatedArgument))]

	@property
	def arg_types(self):
		r = []
		for i in self.args:
			t = (i.ch.type if not isinstance(i, UnevaluatedArgument) else i.ch.argument.ch.type).compiled
			r.append(t)
		#log(str(r))
		return r

	@property
	def sig(self):
		compiled_sig = self.ch.sig.compiled
		if not isinstance(compiled_sig, List):
			log("sig did not compile to list but to " +str(compiled_sig))
			return [Text("bad sig")]#no parent..
		r = [i.compiled for i in compiled_sig]
		for i in r:
			if not isinstance(i, (UnevaluatedArgument, TypedArgument, Text)):
				return [Text("bad sig")]#no parent..
		rr = []
		for i in r:
			if isinstance(i, (UnevaluatedArgument, TypedArgument)):
				t = (i.ch.type if not isinstance(i, UnevaluatedArgument) else i.ch.argument.ch.type).compiled
				if not is_type(t):
					rr.append(Text(" ????? "))
				else:
					rr.append(i)
			else:
				rr.append(i)
		return rr

	@property
	def vardecls(s):
		r = [i if isinstance(i, TypedArgument) else i.ch.argument for i in s.args]
		#print ">>>>>>>>>>>", r
		return r

	def typecheck(self, args):
		for i, arg in enumerate(args):
			#if not arg.type.eq(self.arg_types[i]):
			if isinstance(self.arg_types[i], Ref):
				#we have a chance to compare those without prolog
				if not arg.decl == self.arg_types[i].target:
					log("well this is bad, decl %s of %s != %s" % (arg.decl, arg, self.arg_types[i].target))
					return Banana(str(arg.decl.name) +" != "+str(self.arg_types[i].name))
		return True

	def call(self, args):
		"""common for all function definitions"""
		evaluated_args = []
		for i, arg in enumerate(args):
			if not isinstance(self.sig[i], UnevaluatedArgument):
				evaluated_args.append(arg.eval())
			else:
				evaluated_args.append(arg.compiled)
		#print evaluated_args ,"<<<"
		#args = [arg.eval() for arg in args]
		assert(len(evaluated_args) == len(self.arg_types))
		r = self._call(evaluated_args )
		assert isinstance(r, Node), "_call returned "+str(r)
		return r

	def _eval(s):
		"""this is when the declaration is evaluated, not when we are called"""
		return Text("OK")

	def unresolvize():
		#return dict(super(FunctionDefinitionBase, self).un,
		return {'resolve': True,
		        'function':True,
		        'sig':self.sig.deconstruct()}#but sig returns a list atm


"""for function overloading, we could have a node that would be a "Variant" of
	an original function, with different arguments.

	the rationale is that the information that a call targets a particular function
	is kept...
	the fact that it might not be obvious that a variant is called should be offsettable with the ide
	"""


class FunctionDefinition(FunctionDefinitionBase):

	def __init__(self, kids):
		super(FunctionDefinition, self).__init__(kids)

	def _call(self, call_args):
		#call copy_args?
		return self.ch.body.run()#Void()#

	def copy_args(self, call_args):
		for ca in call_args:
			name = ca.ch.name.pyval
			assert isinstance(name, str)#or maybe unicode
			for vd in self.vardecls:
				if vd.ch.name.pyval == name:
					vd.runtime.value.append(ca.copy())


SyntaxedNodecl(FunctionDefinition,
			   [TextTag("deffun:"), ChildTag("sig"), TextTag(":\n"), ChildTag("body")],
				{'sig': b['function signature list'],
				 'body': b['statements']})


"""
class PassedFunctionCall(Syntaxed):
	def __init__(self, definition):
		super(FunctionCall, self).__init__()
		assert isinstance(definition, FunctionDefinition)
		self.definition = definition
		self.arguments = List([Placeholder() for x in range(len(self.definition.signature.items.items))], vertical=False) #todo:filter out Texts

	def render(self):
		r = ['(call)']
		for i in self.definition.signature.items:
			if isinstance(i, Text):
				r += [(i.widget.text)]
			elif isinstance(i, ArgumentDefinition):
				r += [ElementTag(self.arguments.items[i])]

		return r
"""


class BuiltinFunctionDecl(FunctionDefinitionBase):
	"""lemon internal builtin function,
	leaves type-checking to the function"""
	def __init__(self, kids):
		self._name = 777
		self.fun = 777
		super(BuiltinFunctionDecl, self).__init__(kids)

	@staticmethod
	def create(name, fun, sig):
		x = BuiltinFunctionDecl.fresh()
		x._name = name
		buildin(x, name)
		x.ch.name.widget.value = name
		x.fun = fun
		x.ch.sig = b['function signature list'].inst_fresh()
		x.ch.sig.items = sig
		for i in sig:
			assert(isinstance(i, (Text, TypedArgument)))
		x.fix_parents()
		b[name] = x

	def _call(self, args):
		return self.fun(args)
		# todo use named *args i guess

	@property
	def name(s):
		return s._name

	def palette(self, scope, text, node):
		return []

#user cant instantiate it, but we make a decl anyway,
#because we need to display it, its in builtins,
#its just like a normal function, FunctionCall can
#find it there..
SyntaxedNodecl(BuiltinFunctionDecl,
			   [TextTag("builtin function"), ChildTag("name"), TextTag(":"), ChildTag("sig")],
				{'sig': b['function signature list'],
				 'name': b['text']})


#lets leave print a BuiltinFunctionDecl until we have type conversions
@topic("output")
def b_print(args):
	o = args[0].to_python_str()
	#print o
	log(o)
	return NoValue()

BuiltinFunctionDecl.create(
	"print",
	b_print,
	[ Text("print"), TypedArgument({'name': Text("expression"), 'type': Ref(b['expression'])})])


class FunctionCall(Node):
	def __init__(self, target):
		super(FunctionCall, self).__init__()
		assert isinstance(target, FunctionDefinitionBase)
		self.target = target
		#print self.target.arg_types
		for i in self.target.arg_types:
			assert not isinstance(i, Parser), "%s to target %s is a dumbo" % (self, self.target)
		self.args = [Parser(v) for v in self.target.arg_types] #this should go to fresh()
		self.fix_parents()

	def deconstruct(s):
		r = super(FunctionCall, s).deconstruct()
		r.update({
			'target': s.target.unresolvize()
		})
		return r

	def fix_parents(s):
		s._fix_parents(s.args)

	def delete_child(self, child):
		for i,a in enumerate(self.args):
			if a == child:
				self.args[i] = Parser(self.target.arg_types[i])
				self.args[i].parent = self
				return

	def _eval(s):
		args = s.args#[i.compiled for i in s.args]
		#log("function call args:"+str(args))
		return s.target.call(args)

	def replace_child(self, child, new):
		assert(child in self.args)
		self.args[self.args.index(child)] = new
		new.parent = self


	def render(self):
		r = []
		sig = self.target.sig
		assert isinstance(sig, list)
		argument_index = 0
		assert len(self.args) == len([a for a in sig if isinstance(a, TypedArgument)])
		for v in sig:
			if isinstance(v, Text):
				r += [TextTag(v.pyval)]
			elif isinstance(v, TypedArgument):
				r += [ElementTag(self.args[argument_index])]
				argument_index+=1
			else:
				raise Exception("item in function signature is"+str(v))
		return r

	@property
	def name(s):
		return s.target.name

	def _flatten(self):
		return [self] + flatten([v.flatten() for v in self.args])

class FunctionCallNodecl(NodeclBase):
	"""offers function calls"""
	def __init__(self):
		super(FunctionCallNodecl, self).__init__(FunctionCall)
		buildin(self, 'call')
		FunctionCall.decl = self
	def palette(self, scope, text, node):
		decls = [x for x in scope if isinstance(x, (FunctionDefinitionBase))]
		return [ParserMenuItem(FunctionCall(x)) for x in decls]

FunctionCallNodecl()


class Clock(Node):
	def __init__(self):
		super(Clock,self).__init__()
		self.datetime = __import__("datetime")
	def render(self):
		return [TextTag(str(self.datetime.datetime.now()))]
	def _eval(self):
		return Text(str(self.datetime.datetime.now()))



class PythonEval(Syntaxed):
	def __init__(self, children):
		super(PythonEval, self).__init__(children)

SyntaxedNodecl(PythonEval,
			   [TextTag("python eval"), ChildTag("text")],
			   {'text': Exp(b['text'])})


class BuiltinPythonFunctionDecl(BuiltinFunctionDecl):
	"""checks args, 
	converts to python values, 
	calls python function, 
	converts to lemon value
	
	this is just a step from user-addable python function
	"""
	def __init__(self, kids):
		self.ret= 777
		self.note = 777
		super(BuiltinPythonFunctionDecl, self).__init__(kids)

	def unresolvize(s):
		r = super(BuiltinPythonFunctionDecl, s).unresolvize()
		r.update({
			'ret': s.ret,
		    'note': s.note,
		    'name': s.name,
		    'fun': s.fun,
		    'sig': s.sig,

		})
		return r

	@staticmethod
	#todo:refactor to BuiltinFunctionDecl.create
	#why do we have 2 kinds of names here?
	def create(fun, sig, ret, name, note):
		x = BuiltinPythonFunctionDecl.fresh()
		x._name = name
		buildin(x)
		x.ch.name.widget.value = fun.__name__
		x.fun = fun
		x.ch.sig = b['function signature list'].inst_fresh()
		x.ch.sig.items = sig
		x.ch.sig.fix_parents()
		for i in sig:
			assert(isinstance(i, (Text, TypedArgument)))
		x.ch.ret = ret
		x.note = note
		x.ret = ret
		x.fix_parents()

	def _call(self, args):
		#translate args to python values, call python function
		checker_result = self.typecheck(args)
		if checker_result != True:
			return checker_result
		args = [arg.pyval for arg in args] #todo implement pyval getter of list
		python_result = self.fun(*args)
		lemon_result = self.ret.inst_fresh()
		lemon_result.pyval = python_result #todo implement pyval assignments
		return lemon_result

	def palette(self, scope, text, node):
		return []


SyntaxedNodecl(BuiltinPythonFunctionDecl,
		[
		TextTag("builtin python function"), ChildTag("name"), 
		TextTag("with signature"), ChildTag("sig"),
		TextTag("return type"), ChildTag("ret")
		],
		{
		'sig': b['function signature list'],
		"ret": b['type'],
		'name': b['text']
		})



def num_arg(name = "number"):
	return TypedArgument({'name':Text(name), 'type':Ref(b['number'])})

def text_arg():
	return TypedArgument({'name':Text("text"), 'type':Ref(b['text'])})

def num_list():
	return  b["list"].make_type({'itemtype': Ref(b['number'])})

def num_list_arg():
	return TypedArgument({'name':Text("list of numbers"), 'type':num_list()})


def add_operators():
	#we'll place this somewhere else, but later i guess, splitting this
	#file into some reasonable modules would still create complications
	import operator as op


	def pfn(function, signature, return_type = int, **kwargs):
		"""helper function to add a builtin python function"""
		if return_type == int:
			return_type = Ref(b['number'])
		elif return_type == bool:
			return_type = Ref(b['bool'])
		#else: assert
		if 'note' in kwargs:
			note = kwargs['note']
		else:
			note = ""
		if 'name' in kwargs:
			name = kwargs['name']
		else:
			name = function.__name__

		BuiltinPythonFunctionDecl.create(
			function,
			signature,
			return_type,
			name,
			note)

	pfn(op.abs, [Text("abs("), num_arg(), Text(")")])
	pfn(op.add, [num_arg(), Text("+"), num_arg()])
	if PY2:
		pfn(op.div, [num_arg(), Text("/"), num_arg()])
	else:
		pfn(op.floordiv, [num_arg(), Text("//"), num_arg()])
		pfn(op.truediv,  [num_arg(), Text("/"), num_arg()])
	
	pfn(op.eq,  [num_arg(), Text("=="), num_arg()], bool)
	pfn(op.ge,  [num_arg(), Text(">="), num_arg()], bool)
	pfn(op.gt,  [num_arg(), Text(">="), num_arg()], bool)
	pfn(op.le,  [num_arg(), Text("<="), num_arg()], bool)
	pfn(op.lt,  [num_arg(), Text("<="), num_arg()], bool)
	pfn(op.mod, [num_arg(), Text("%"), num_arg()])
	pfn(op.mul, [num_arg(), Text("*"), num_arg()])
	pfn(op.neg, [Text("-"), num_arg()])
	pfn(op.sub, [num_arg(), Text("-"), num_arg()])

	#import math

	def b_squared(arg):
		return arg * arg
	pfn(b_squared, [num_arg(), Text("squared")], name = "squared")

	def b_list_squared(arg):
		return [b_squared(i) for i in arg]
	pfn(b_list_squared, [num_list_arg(), Text(", squared")], num_list(), name = "squared")

	pfn(sum, [Text("the sum of"), num_list_arg()], name = "summed")

	def b_range(min, max):
		return list(range(min, max + 1))
	pfn(b_range, [Text("numbers from"), num_arg('min'), Text("to"), num_arg('max')],
		num_list(), name = "range", note="inclusive")


add_operators()


"""
we got drunk and wanted to implement regex input. i will hide this in its own module asap.
"""
#regex is list of chunks
#chunk is matcher + quantifier | followed-by
#matcher is:
#chars
#range
#or

SyntacticCategory({'name': Text("chunk of regex")})
SyntacticCategory({'name': Text("regex quantifier")})
SyntacticCategory({'name': Text("regex matcher")})
#WorksAs.b("expression", "statement")

class Regex(Syntaxed):
	pass

SyntaxedNodecl(Regex,
	[ChildTag('chunks')],
	{'chunks': b["list"].make_type({'itemtype': Ref(b['chunk of regex'])})})

class RegexFollowedBy(Syntaxed):
	pass
SyntaxedNodecl(RegexFollowedBy,
	["followed by"],
	{})

class QuantifiedChunk(Syntaxed):
	 pass
SyntaxedNodecl(QuantifiedChunk,
	[ChildTag("quantifier"), ChildTag("matcher")],
	{"quantifier": b['regex quantifier'],
	"matcher": b['regex matcher']})

class UnquantifiedChunk(Syntaxed):
	pass
SyntaxedNodecl(UnquantifiedChunk,
	[ChildTag("matcher")],
	{"matcher": b['regex matcher']})

#i skew the grammar a bit so it will be easier to construct things in the stupid gui#kay
#normally i think it would be defined #hmm nvm

class RegexZeroOrMore(Syntaxed):
	pass
SyntaxedNodecl(RegexZeroOrMore,
	['zero or more'],{})

class RegexChars(Syntaxed):
	pass
SyntaxedNodecl(RegexChars,
	[ChildTag("text")],
	{'text': b['text']})
class RegexRange(Syntaxed):
	pass
SyntaxedNodecl(RegexRange,
	['[', ChildTag("text"), ']'],
	{'text': b['text']})



def b_match(regex, text):
	import re
	#...

BuiltinPythonFunctionDecl.create(
	b_match, 
	[
	Text('number of matches of'),
	TypedArgument({'name': Text('regex'), 'type':Ref(b['regex'])}),
	Text('with'), 
	TypedArgument({'name': Text('text'), 'type':Ref(b['text'])})],
	Ref(b['number']), #i should add bools and more complex types........
	"match",
	"regex")


"""
Quantifiers
'a?' : 'a' 0 or 1 times
'a*' : 'a' 0 or more times
'a+' : 'a' 1 or more times
'a{9}': 2 'a's
'a{2, 9}': between 2 and 9 'a's
'a{2,}' : 2 or more 'a's
'a{,5}' : up to 5 'a's

Ranges:
'[a]': 'a'
'[a-z]': anything within the letters 'a' to 'z'
'[0-9]': same, but with numbers
'(a)' : 'a'#group?yes#ok no groups for us for now
'(a|b|c)': 'a' or 'b' or 'c'#i think this should be kept, because i think it
is the only way to match a quantity of alternations#i see
'a|b' : 'a' or 'b' (without group)
'^a' : 'a' at start of string
'a$' : 'a' at end of string

Tah-dah!#you really like typing.
"""

#alright
#about time to split nodes.py into modules....
#hmm
#bet you 5 bucks this wont run:D
#if i copy paste this into my IDE, fix up the code above and it runs, do you owe me?
#no
#damn
#lets try running it :P
#not yet..
#but lets do it here
#but it's probably a valid lemon program



class Note(Syntaxed):
	def __init__(self, kids):
		self.text = widgets.Text(self, "")
		super(Note,self).__init__(kids)

SyntaxedNodecl(Note,
			   [["note: ", WidgetTag("text")]],
			   {'text': Exp(b['text'])})


class Annotation(Node):
	def __init__(self, target, text):
		self.text = text
		self.target = target
		super(Annotation,self).__init__()

	def render(s):
		return [ArrowTag(s.target), TextTag(s.text)]



class ShellCommand(Syntaxed):
	info = ["runs a command with os.system"]
	def __init__(self, kids):
		super(ShellCommand, self).__init__(kids)

	def _eval(s):
		cmd = s.ch.command.eval()
		import os
		try:
			return Text(str(os.system(cmd.pyval)))
		except Exception as e:
			return Text(str(e))

SyntaxedNodecl(ShellCommand,
			   [["bash:", ChildTag("command")]],
			   {'command': Exp(b['text'])})


class FilesystemPath(Syntaxed):
	def __init__(self, kids):
		self.status = widgets.Text(self, "(status)")
		self.status.color = "compiler hint"
		super(FilesystemPath, self).__init__(kids)

	def _eval(s):
		p = s.ch.path.eval().pyval
		from os import path
		s.status.text = "(valid)" if path.exists(p) else "(invalid)"
		return Text(p)


SyntaxedNodecl(FilesystemPath,
			   [[ChildTag("path")],
			    [ChildTag("path"), WidgetTag("status")]],
			   {'path': Exp(b['text'])})

def b_files_in_dir(dir):
	import os
	for x in os.walk(dir):
		return x[2]
	return []

BuiltinPythonFunctionDecl.create(b_files_in_dir, [Text("files in"), text_arg()], list_of('text'), "list files in dir", "ls, dir")




class Lesh(Node):
	"""just another experiment: independent of the lemon language,
	this is a command line that calls bash to execute commands.
	a variation on shell snippets for fish / betty
	lemon would probably make it more natural to have to option to insert
	either raw text or a "human" snippet form, like <count lines>,
	and toggle them freely
	"""
	#might add history later or xiki style?
	def __init__(s):
		super(Lesh, s).__init__()
		s.command_line = LeshCommandLine()
		s.command_line.parent = s


	def render(self):
		return [TextTag("just a little experiment, a frontend for bash/fish/zsh that lets you insert snippets and stuff:\n"),
		                WidgetTag('command_line')]

class LeshSnippetDeclaration(Syntaxed):
	"""a declaration of a snippet"""
	def __init__(self, kids):
		super(LeshSnippetDeclaration, self).__init__(kids)
	@property
	def human(s):
		return s.ch.human.pyval
	@property
	def command(s):
		return s.ch.command.pyval

	def palette(self, scope, text, node):
		return [LeshMenuItem(self)]

SyntaxedNodecl(LeshSnippetDeclaration,
				[[ChildTag("human"), ChildTag("command")]],
				{'human': b['text'], #add more wordings later
				'command': b['text']})

for h,c in [
	("count words", "wc"),
	("mount all", "mount -a")

	]:
		buildin(LeshSnippetDeclaration({'human':Text(h), 'command':Text(c)}))#for now

class LeshSnippet(Node):
	"""for the case you want to insert the snippet in the human readable form"""
	def __init__(self, declaration):
		super(LeshSnippet, self).__init__()
		self.declaration = declaration

#todo: alt insert mode
#todo: split on pipes



#Const({'name': Text("meaning of life"), 'value': Number(42)})
"""the end"""

def make_root():
	global building_in
	r = Root()
	r.add(("welcome", Text("Welcome to lemon! Press F1 to cycle the sidebar!")))
	r.add(("lesh", Lesh()))
	r.add(("some program", b['module'].inst_fresh()))
	r["some program"].ch.statements.newline()
	r.add(("builtins", b['module'].inst_fresh()))
	r["builtins"].ch.statements.items = list(itervalues(b))#hm
	r["builtins"].ch.statements.add(Text("---end of builtins---"))
	r["builtins"].ch.statements.view_mode = 2
	building_in = False

	#r.add(("toolbar", toolbar.build()))
	#test_serialization(r)
	return r



def to_lemon(x):
	print ("to-lemon", x)
	if isinstance(x, str_and_uni):
		return Text(x)
	elif isinstance(x, (int, float)):
		return Number(x)
	else:
		raise Exception("i dunno how to convert that")
	#elif isinstance(x, list):


def is_flat(l):
	return flatten(l) == l

"""
def ph_to_lemon(x):
	return iter([to_lemon(x)])


if __name__ == "__main__":
	print "testing.."
	e = uni.Engine("""
"""

do(1, A) :-
	python:to_lemon(3, A).
%	python:print(A).

"""
""", globals())

	print [x for x in e.db.do.iter(1, None)]
"""


"""
#todo: totally custom node:
we have unevaluated arguments, so a function body can be thought of as a rule for
evaluating the node. there could be other rules: display, debugging..?..
"""


"""todo:
modules: how to declare imports, how to denote in menu items that a function is
from some module..
ipython parallel/pyrex/something distributedness
dbpedia node
curses, js(brython seems nice) frontends

"""

#maybe todo: make the calls to builtin explicit, not hidden in constructors
"""todo: decide if declarative nodes like SyntacticCategory and Definition should have
the name as a child node...it doesnt seem to make for a clear reading"""
