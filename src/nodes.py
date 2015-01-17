# -*- coding: utf-8 -*-

"""

this file defines the AST classes of the language and everything around it.
the philosophy of this codebase is "constant surprise". it keeps you alert.
"kids" and "children" mean the same.
sometimes i use "s" instead of "self".
"ch" is children of syntaxed.
good luck.

"""

# region imports

import json
from types import SimpleNamespace

from fuzzywuzzy import fuzz
from pizco import Signal

from lemon_utils.lemon_six import iteritems, iterkeys, itervalues, unicode
from lemon_utils.notifyinglist import NotifyingList

import element
from menu_items import MenuItem
import widgets
import tags
from tags import *

from lemon_colors import colors
from keys import *
from lemon_utils.utils import flatten, odict, Evil, uniq
from lemon_utils.dotdict import Dotdict
from lemon_args import args
from lemon_utils.lemon_logging import log, warn

from marpa_cffi.marpa_misc import * # valuator actions

tags.asselement = element # for assertions

# endregion
AST_CHANGED = 2

#B is for staging the builtins module and referencing builtin nodes from python code
B = Dotdict()
B._dict = odict()

def build_in(node, name=None):
	"""add node to B"""
	if isinstance(node, list):
		[build_in(node) for node in node]
	else:
		if name == False or isinstance(node, Text):
			key = node # we wont need to reference this node, so any useless key will do
		elif name == None:
			key = node.name
		else:
			key = name
		if isinstance(key, unicode):
			key = key.replace(' ', '_')
		assert node
		assert key,  key
		assert key not in B._dict,  repr(key) + " already in builtins:" + repr(node)
		B[key] = node
	return node

# region utils

def is_decl(node):
	return isinstance(node, (NodeclBase, ParametricTypeBase, ParametricNodecl))
def is_type(node):
	return is_decl(node) or isinstance(node, (Ref, Exp, Definition, SyntacticCategory, EnumType))

def deref_decl(d):
	if isinstance(d, Ref):
		return deref_decl(d.target)
	elif isinstance(d, Definition):
		return deref_decl(d.type)
	elif is_decl(d) or d == None:
		return d
	else:
		raise Exception("i dont knwo how to deref "+repr(d)+", it should be a type or something")

def make_list(type_name= 'anything'):
	"instantiate a lemon List of given type"
	return list_of(type_name).inst_fresh()

def list_of(type_name):
	"""a helper for creating a type"""
	return B.list.make_type({'itemtype': Ref(B[type_name])})

def dict_from_to(key, val):
	"""a helper for creating a type"""
	return B.dict.make_type({'keytype': Ref(B[key]), 'valtype': Ref(B[val])})

def make_dict(key_type_name, val_type_name):
	return dict_from_to(key_type_name, val_type_name).inst_fresh()

def make_dict_from_anything_to_anything():
	return make_dict('anything', 'anything')

def new_module():
	return B.module.inst_fresh()

def is_flat(l):
	return flatten(l) == l

def to_lemon(x):
	r = _to_lemon(x)
	log ("to-lemon(%s) -> %s"%(x,r))

	return r

def _to_lemon(x):
	if isinstance(x, unicode):
		return Text(x)
	elif isinstance(x, bool):
		if x:
			return EnumVal(B.bool, 1)
		else:
			return EnumVal(B.bool, 0)
	elif isinstance(x, (int, float)):
		return Number(x)
	elif isinstance(x, dict):
		r = dict_from_to('anything', 'anything').inst_fresh()
		r.pyval = x
		return r
	elif isinstance(x, list):
		r = list_of('anything').inst_fresh()
		r.pyval = x
		return r
	else:
		raise Exception("i dunno how to convert %s"%repr(x))
	#elif isinstance(x, list):

class Children(Dotdict):
	"""this is the "ch" of Syntaxed nodes"""
	pass


# endregion

# region persistence

class DeserializationException(Exception):
	pass

def deserialize(data, parent):
	"""
	data is a json.load'ed .lemon file
	parent is a dummy node placed at the point where the deserialized node should go,
	this makes things like List.above() work while getting scope
	"""

	if 'resolve' in data: # create a Ref pointing to another node
		return resolve(data, parent)
	if not 'decl' in data: # every node must have a type
		raise DeserializationException("decl key not in found in %s"%data)
	decl = data['decl']
	log("deserializing node with decl %s"%decl)
	if decl == 'Parser': # ok, some nodes are special, we dont have a type for Parser
		return Parser.deserialize(data, parent)
	if decl == 'defun': # or defun..apparently..
		return FunctionDefinitionBase.deserialize(data, parent)
	#if decl == 'varref':
	#	return VarRef.deserialize(data, parent)
	if isinstance(decl, unicode): # we will look for a nodecl node with this name
		decl = find_decl(decl, parent.nodecls)
		if decl:
			log("deserializing item with decl %s thru class %s"%(decl, decl.instance_class))
			return decl.instance_class.deserialize(data, parent)
		else:
			raise DeserializationException ("cto takoj " + repr(decl))
	elif isinstance(decl, dict): # the node comes with a decl as, basically, its child
		decl = deserialize(decl, parent)
		try:
			return deref_decl(decl).instance_class.deserialize(data, parent)
		except DeserializationException as e:
			log(e)
			return failed_deser(data)
	else:
		raise DeserializationException ("cto takoj " + repr(decl))

def failed_deser(data):
	"""create a Serialized node that holds the data that failed to deserialize"""
	r = Serialized.fresh()
	if 'last_rendering' in data:
		r.ch.last_rendering.pyval = data['last_rendering']
	r.ch.serialization = to_lemon(data)
	r.fix_parents()
	return r


def find_decl(name, decls):
	"""find decl by name"""
	assert isinstance(name, unicode)
	for i in decls:
		if name == i.name:
			log("found",name)
			return i
	raise DeserializationException ("%s not found in %s"% (repr(name), repr(decls)))


def resolve(data, parent):

	assert(data['resolve'])
	log("resolving", data)
	scope = parent.scope()

	if 'decl' in data:
		decl = data['decl']
		if decl == "defun":
			#lets make functions hacky so that its not specified in the save file if
			#its a built in or a defined one etc.
			return resolve_function(data, parent)

		elif isinstance(decl, dict):
			placeholder = Text("placeholder")
			placeholder.parent = parent
			decl = deserialize(decl, placeholder)

			name = data['name']

			for i in scope:
				#if decl.eq(i.decl) and i.name == name:
				log(deref_decl(decl) ,deref_decl(i.decl))
				if deref_decl(decl) == deref_decl(i.decl):
					log("in scope:",i)
					if i.name == name:
						return i
			raise DeserializationException("node not found: %s ,decl: %s"%(data,decl))

	elif 'class' in data:
		name = data['name']
		c = data['class']
		for i in scope:
			#log(i.__class__.__name__.lower(), c)
			if i.__class__.__name__.lower()  == c and i.name == name:
				return i
		raise DeserializationException("node with name %s and class %s not found"%(name,c))

	else:
		raise DeserializationException("dunno how to resolve %s" % data)


#these PersistenceStuff classes are just bunches of functions
#that could as well be in the node classes themselves,
#the separation doesnt have any function besides having them all
#in one place for convenience

class NodePersistenceStuff(object):
	def serialize(s):
		#assert isinstance(s.decl, Ref) or s.decl.parent == s,  s.decl
		return odict(
			s.serialize_decl()).updated_with(s._serialize())

	def serialize_decl(s):
		if s.decl:
			log("serializing decl %s of %s"%(s.decl, s))
			return {'decl': s.decl.serialize()}
		else:
			return {'class': s.__class__.__name__.lower()}

	def unresolvize(s):
		return odict(
			resolve = True,
			name = s.name).updated_with(s.serialize_decl())

	def _serialize(s):
		return {}


class SyntaxedPersistenceStuff(object):
	def _serialize(s):
		return odict(
			children = s.serialize_children()
		)

	def serialize_children(s):
		r = {}
		for k, v in iteritems(s.ch._dict):
			r[k] = v.serialize()
		return r

	@classmethod
	def deserialize(cls, data, parent):
		r = cls.fresh()
		r.parent = parent
		for k,v in iteritems(data['children']):
			r.set_child(k, deserialize(v, r))
		return r


class ListPersistenceStuff(object):
	def _serialize(s):
		return odict(
			items = [i.serialize() for i in s.items]
		)


	@classmethod
	def deserialize(cls, data, parent):
		r = cls()
		assert(r.items == [])
		r.parent = parent

		placeholder = Text("placeholder")
		placeholder.parent = parent
		r.decl = deserialize(data['decl'], placeholder)

		for i, item_data in enumerate(data['items']):
			r.add(Text("placeholder"))
			r.items[i] = deserialize(item_data, r.items[i])
		return r

class BaseRefPersistenceStuff(object):
	pass

class RefPersistenceStuff(BaseRefPersistenceStuff):
	def serialize(s):
		return odict(
			decl = 'ref',
			target = s.target.unresolvize())

	def unresolvize(s):
		return s.serialize()

	@classmethod
	def deserialize(cls, data, parent):
		placeholder = Text("placeholder")
		placeholder.parent = parent
		target = deserialize(data['target'], placeholder)
		r = cls(target)
		r.parent = parent
		return r


class VarRefPersistenceStuff(BaseRefPersistenceStuff):
	def _serialize(s):
		return odict(
			target = s.target.unresolvize())

	@classmethod

	def deserialize(cls, data, parent):
		placeholder = Text("placeholder")
		placeholder.parent = parent
		decl = deserialize(data['target']['decl'], placeholder)
		for i in parent.vardecls_in_scope:
			log(i)
			if decl.eq_by_value_and_python_class(i.decl):
				if i.name == data['target']['name']:
					r = cls(i)
					r.parent = parent
					return r
		raise DeserializationException ("vardecl not found:%s"%data)


class ParserPersistenceStuff(object):
	def serialize(s):
		return odict(
			decl = 'Parser',
		    slot = s.slot,
			items = s.serialize_items()
		)

	def serialize_items(s):
		r = []
		for i in s.items:
			#log("serializing " + str(i))
			if isinstance(i, unicode):
				r.append(i)
			else:
				r.append(i.serialize())
		return r

	@classmethod
	def deserialize(cls, data, parent):
		r = cls(data['slot'])
		r.parent = parent
		log("deserializing Parser "+str(data))
		for i in data['items']:
			if isinstance(i, unicode):
				r.add(i)
			else:
				r.add(deserialize(i, r))
		r.fix_parents()
		return r


class FunctionCallPersistenceStuff(object):
	def _serialize(s):
		return odict(
			target = s.target.unresolvize(),
		    args = s.serialize_args()

		)

	def serialize_args(s):
		return dict([(k, i.serialize()) for k,i in iteritems(s.args)])

	@classmethod
	def deserialize(cls, data, parent):
		placeholder = Text("placeholder")
		placeholder.parent = parent
		r = cls(deserialize(data['target'], placeholder))
		r.parent = parent
		for k,v in iteritems(data['args']):
			r.args[k] = deserialize(v, r.args[k])
		return r

def resolve_function(data, parent):
	scope = parent.scope()
	funcs = [i for i in scope if isinstance(i, FunctionDefinitionBase)]
	if 'name' in data:
		for i in funcs:
			if i.name == data['name']:
				#log("found")
				return i
		raise DeserializationException("function %s not found by name" % data)
	elif 'sig' in data:
		sig = deserialize(data['sig'], parent)
		assert isinstance(sig, List)
		for i in funcs:
			if i.ch.sig.eq_by_value_and_python_class(sig):
				#log("found")
				return i
		raise DeserializationException("function %s not found by sig" % data)

	else:
		raise DeserializationException("function call without neither sig nor name:%s" % data)

class BuiltinFunctionDeclPersistenceStuff(object):
	def serialize(s):
		return odict(decl = 'defun', name=s.name)

	def unresolvize(s):
		return s.serialize()

class FunctionDefinitionPersistenceStuff(object):
	def unresolvize(s):
		return odict(resolve = True, decl = 'defun', sig=s.ch.sig.serialize())


class WidgetedValuePersistenceStuff(object):

	def _serialize(s):
		return odict(text = s.widget.text)

	@classmethod
	def deserialize(cls, data, parent):
		r = cls()
		log(data)
		r.text = data['text']
		r.parent = parent
		return r

# endregion

# region basic node classes

class Node(NodePersistenceStuff, element.Element):
	"""a node is more than an element,
	nodes can added, cut'n'pasted around, evaluated etc.
	every node class has a corresponding decl object...almost
	"""
	easily_instantiable = False
	isconst = False
	brackets_color = colors.node_brackets

	def __init__(self):
		"""	__init__ usually takes children or value as arguments.
		fresh() calls it with some defaults (as the user would have it inserted from the menu)
		each class has a decl, which is an object descending from NodeclBase (nodecl for node declaration).
		nodecl can be thought of as a type, and objects pointing to them with their decls as values of that type.
		nodecls have a set of functions for instantiating the values, and those need some cleanup"""
		super().__init__()
		self.runtime = Dotdict() #various runtime data herded into one place
		self.clear_runtime_dict()
		self.fresh = "i think youre looking for inst_fresh, fresh() is a class method, you called it on an instance"
		self.forget_symbols()

	def forget_symbols(s):
		"""clear marpa symbol ids"""
		s._symbol  = None

	@property
	def symbol(s):
		#log("gimme node_symbol")
		if s._symbol == None:
			s.register_symbol()
		return s._symbol

	def register_symbol(s):
		#log("default")
		pass

	@classmethod
	def register_class_symbol(cls):
		pass

	"""
	def make_rainbow(s):
		try:#hacky rainbow depending on the colors module
			c = colors.color("node brackets")
			hsv = tuple(colors.rgb(*c).hsv)
			hsv2 = colors.hsv((hsv[0] + 0.3*s.number_of_ancestors)%1, hsv[1], hsv[2])
			r = hsv2.rgb
			return (int(r.red), int(r.green), int(r.blue))
		except:
			#return colors.color("fg")
			return "fg"

	@property
	def brackets_color(s):
		if s._brackets_color == "node brackets rainbow":
			#this is slow as fuck, lets 'cache' it for now
			s._brackets_color = s.make_rainbow()
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
	"""

	def clear_runtime_dict(s):
		s.runtime._dict.clear()

	def set_parent(s, v):
		assert v or isinstance(s, Root),  s
		super(Node, s).set_parent(v)
		if "value" in s.runtime._dict: #crap
			s.runtime.value.parent = s.parent

	#overriding properties has to be done like this
	parent=property(element.Element.get_parent, set_parent)

	@property
	def parsed(s):
		"all nodes except Parser return themselves"#..hm
		return s

	def scope(self):
		"""lexical scope, what does this node see?"""
		r = []

		if isinstance(self.parent, List):
			r += [x.parsed for x in self.parent.above(self)]

		assert self.parent != None, self.long__repr__()
		r += [self.parent]
		r += self.parent.scope()

		assert(r != None)
		assert(flatten(r) == r)
		return r

	@property
	def nodecls(s):
		return [i for i in s.scope() if isinstance(i, NodeclBase)] #crap:just NodeclBase? what about EnumType?

	@property
	def vardecls_in_scope(self):
		"""what variable declarations does this node see?"""
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
		"call _eval(), save result to self.runtime"
		r = self._eval()
		assert isinstance(r, Node),  str(self) + "._eval() is borked"

		#if self.isconst: # todo:figure out how const would propagate (to compiler)
		#	self.runtime.value.set(r)
			#log("const" + str(self))
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

	def module(self):
		if isinstance(self, Module):
			return self
		else:
			if self.parent != None:
				return self.parent.module()
			else:
				log ("%s has no parent", self)
				return None

	@classmethod
	def fresh(cls, decl=None):
		"make a new instance"
		r = cls()
		if decl:
			r.decl = decl
		return r

	def to_python_str(self):
		return unicode(self)

	@property
	def vardecls(s):
		"""what variables does this node declare"""
		return []

	def tags(elem):
		"""called from Element.render"""
		yield super().tags()
		#results of eval
		if "value" in elem.runtime._dict \
				and "evaluated" in elem.runtime._dict \
				and not isinstance(elem.parent, Parser): #dont show evaluation results of parser's direct children
			yield [AttTag(Att.elem, elem), ColorTag(colors.eval_results), TextTag("->")]
			v = elem.runtime.value
			if len(v.items) > 1:
				yield [TextTag(str(len(v.items))), TextTag(" values:"), ElementTag(v)]
			else:
				for i in v.items:
					yield ElementTag(i)
			yield [TextTag(":"), EndTag(),EndTag()]

	#i dont get any visitors here, nor should my code
	def flatten(self):
		"""return yourself and all your children/items as a list
		#crap: decls arent included in flatten(?)
		"""
		return flatten(self._flatten())

	def _flatten(self):
		"per-class implementation of flattening"
		if not isinstance(self, (WidgetedValue, EnumVal, Ref, SyntaxedNodecl, FunctionCallNodecl,
			ParametricNodecl, Nodecl, VarRefNodecl, TypeNodecl, VarRef)): #all childless nodes
			warn(str(self)+ " flattens to self")
		return [self]

	def palette(self, scope, text, node):
		"create menu items"
		return []

	def __repr__(s):
		r = object.__repr__(s)
		try:
			r += "("+s.name+")"
		except: # no name
			pass
		return r

	@property
	def ddecl(s):
		"""decl dereferenced to the actual value, thru refs/definitions.."""
		return deref_decl(s.decl)#i have no idea what im doing

	def eq_by_value_and_python_class(a, b):
		"""like comparing by type and value, but crappier"""
		a,b = a.parsed, b.parsed
		if a.__class__ != b.__class__:
			return False
		return a.eq_by_value(b)

	def delete_child(self, child):
		log("not implemented, go delete someone else's children")


class Syntaxed(SyntaxedPersistenceStuff, Node):
	"""
	Syntaxed has some named children, kept in self.ch.
	their types are in self.slots.
	syntax is a list of Tags, and it can contain ChildTag
	"""
	def __init__(self, children):
		super(Syntaxed, self).__init__()
		self.check_slots(self.slots)
		self.syntax_index = 0
		self.ch = Children()

		assert len(children) == len(self.slots)

		#set children from the constructor argument
		for k in iterkeys(self.slots):
			self.set_child(k, children[k])

		# prevent setting new ch keys
		self.ch._lock()
		# prevent setting new attributes
		self.lock()
		#assert isinstance(self.ddecl, SyntaxedNodecl)
	"""
	@classmethod
	def register_class_symbol(cls):
		r = m.symbol(cls.__name__)
		syms = []
		for i in deref_decl(cls.decl).instance_syntaxes[0]:
			if type(i) == unicode:
				syms.append(m.known_string(i))
			elif type(i) == Exp:
				syms.append(B.anything.sym)
			else:
				syms.append(i.symbol)
		m.rule(r, "", r, syms)
	"""


	def fix_parents(self):
		self._fix_parents(list(self.ch._dict.values()))

	def set_child(self, name, item):
		assert isinstance(name, unicode), repr(name)
		assert isinstance(item, Node)
		item.parent = self
		self.ch[name] = item

	def replace_child(self, child, new):
		"""child name or child value? thats a good question...its child the value!"""
		assert(child in itervalues(self.ch))
		assert(isinstance(new, Node))
		for k,v in iteritems(self.ch):
			if v == child:
				self.ch[k] = new
				new.parent = self
				return
		raise Exception("i dont have that child: "+child)
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
				assert(isinstance(name, unicode))
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
		return CHANGED

	def next_syntax(self):
		self.syntax_index  += 1
		if self.syntax_index == len(self.syntaxes):
			self.syntax_index = len(self.syntaxes)-1
		log("next syntax")
		return CHANGED

	@classmethod
	def create_kids(cls, slots):
		cls.check_slots(slots)
		kids = {}
		for k, v in iteritems(slots):
			#print v # and : #todo: definition, syntaxclass. proxy is_literal(), or should that be inst_fresh?
			try:
				easily_instantiable = deref_decl(v).instance_class.easily_instantiable
			except:
				easily_instantiable = False
			if easily_instantiable:
				a = v.inst_fresh()
#			elif isinstance(v, ParametricType):
#				a = v.inst_fresh()
			else:
				a = Parser(k)
			assert(isinstance(a, Node))
			kids[k] = a
		return kids

	@classmethod
	def fresh(cls, decl=None):
		r = cls(cls.create_kids(deref_decl(cls.decl).instance_slots))
		if decl:
			r.decl = decl
		r.fix_parents()
		return r

	@property
	def name(self):
		"""override if this doesnt work for your subclass"""
		return self.ch.name.pyval

	@property
	def syntaxes(self):
		return self.ddecl.instance_syntaxes

	@property
	def slots(self):
		return self.ddecl.instance_slots

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.ch)+"')"

	def eq_by_value(a, b):
		assert len(a.ch._dict) == len(b.ch._dict) #are you looking for eq_by_value_and_decl?
		for k,v in iteritems(a.ch._dict):
			if not b.ch[k].eq_by_value_and_python_class(v):
				return False
		return True

	def copy(s):
		if isinstance(s.decl, Ref):
			decl = s.decl.copy()
		else:
			decl = s.decl
		r = s.__class__.fresh(decl)
		for k,v in iteritems(s.ch._dict):
			r.ch[k] = v.copy()
		r.fix_parents()
		return r


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
		yield [MemberTag('view_mode_widget')] + [IndentTag()]
		if self.view_mode > 0:
			if self.view_mode == 2:
				yield TextTag("\n")
			yield self.render_items()
		yield [DedentTag()]

	@classmethod
	def fresh(cls, decl):
		#log("decl="+repr(decl))
		r = cls()
		if decl:
			r.decl = decl
		assert(r.decl)
		return r

class Dict(Collapsible):
	def __init__(self):
		super(Dict, self).__init__()
		self.items = odict()

	def render_items(self):
		r = []
		for key, item in iteritems(self.items):
			r += ['\n'] # this *could* be a Dict one day, but its only used for Root now
			r += [{'font_level':1}, ElementTag(key), TextTag(":")]#, IndentTag(), NewlineTag()]
			r += [ElementTag(item)]
			#r += [DedentTag(), NewlineTag()]
		return r

	def find(s, key):
		for k in iterkeys(s.items):
			if k.eq_by_value_and_python_class(key): #should be by decl
				return k

	def __getitem__(s, key):
		#as a special hack,
		if isinstance(key, unicode):
			key = Text(key, debug_note="created in Dict.find")

		k = s.find(key)
		if k != None:
			return s.items[k]
		else:
			raise Exception("nope")

	def __setitem__(s, key, val):
		#as a special hack,
		if isinstance(key, unicode):
			key = Text(key, debug_note="created in Dict.find")

		k = s.find(key)
		if k != None:
			key = k
		else:
			key.parent = s
		s.items[key] = val
		val.parent = s

	def fix_parents(self):
		super(Dict, self).fix_parents()
		self._fix_parents(list(self.items.values()))
		self._fix_parents(list(self.items.keys())) # why so complicated?

	def _flatten(self):
		return ([self] + \
		       [k.flatten() for k in iterkeys(self.items)] +
		       [v.flatten() for v in itervalues(self.items) if isinstance(v, Node)])#skip Widgets, for Settings

	@property
	def pyval(self):
		r = {}
		for k,v in iteritems(self.items):
			r[k.pyval] = v.pyval
		return r

	@pyval.setter
	def pyval(self, val):
		new = odict()
		for k, v in iteritems(val):
			new[to_lemon(k)] = to_lemon(v)
		self.items = new
		self.fix_parents()

	"""
	def add(self, kv):
		key, val = kv
		assert(key not in self.items)
		self.items[key] = val
		assert(isinstance(key, unicode))
		assert(isinstance(val, element.Element))
		val.parent = self
		return val
	"""

class List(ListPersistenceStuff, Collapsible):
	easily_instantiable = True
	#todo: view sorting
	def __init__(self):
		super(List, self).__init__()
		self.items = []
		self.decl = Ref(B.anything)

	@classmethod
	def register_class_symbol(cls):
		log("registering list grammar")
		optionally_elements = m.symbol('optionally_elements')
		m.sequence('optionally_elements', optionally_elements, B.anything.symbol, ident_list, m.known_char(','), 0)
		r = m.symbol('list literal')
		opening =  m.known_char('[')
		closing =  m.known_char(']')
		m.rule('list literal', r, [opening, optionally_elements, closing], cls.from_parse)
		return r

	@classmethod
	def from_parse(cls, x):
		log('from_parse:%s',x)
		assert x[0] == '['
		assert x[2] == ']'
		assert type(x[1]) == list
		r = List()
		r.items = x[1][::2]
		r.view_mode = r.vm_multiline
		return r

	def render_items(self):
		#we will have to work towards having this kind of syntax
		#defined declaratively so Parser can deal with it
		yield TextTag('[')
		for item in self.items:
			yield [ElementTag(item)]
			if self.view_mode == 2:
				yield '\n'
			else:
				yield TextTag(', ')
		yield TextTag(']')

	def __getitem__(self, i):
		return self.items[i]

	def __setitem__(self, i, v):
		self.items[i] = v
		v.parent = self

	def fix_parents(self):
		super(List, self).fix_parents()
		self._fix_parents(self.items)

	@property
	def slots(s):
		return [s.item_type]

	def item_index(self, atts):
		#for atts in [atts.middle, atts.left, atts.right]:
		li = atts.get('list_item')
		if li and li[0] == self:
			return li[1]

	def _eval(self):
		r = List()
		r.decl = self.decl.copy()
		r.items = [i.eval() for i in self.items]
		r.fix_parents()
		return r

	def copy(self):
		r = List()
		r.decl = self.decl.copy()
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

	def newline(self, pos=-1):
		p = Parser(0)
		p.parent = self
		self.items.insert(pos, p)
		return p

	def newline_with(self, node):
		self.newline.add(node)

	@property
	def item_type(self):
		assert hasattr(self, "decl"),  "parent="+str(self.parent)+" contents="+str(self.items)
		ddecl = self.ddecl
		assert isinstance(ddecl, ParametricType), self
		r = self.ddecl.ch.itemtype
		#log('item_type',r)
		return r

	def above(self, item):
		assert item in self.items,  (item, item.parent)
		r = []
		for i in self.items:
			if i == item:
				return r
			else:
				r.append(i)

	def below(self, item):
		assert item in self.items,  (item, item.parent)
		return self.items[self.items.index(item):]

	def to_python_str(self):
		return "[" + ", ".join([i.to_python_str() for i in self.items]) + "]"

	def delete_child(s, ch):
		if ch in s.items:
			s.items.remove(ch)

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.item_type)+"')"

	@property
	def val(self):
		"""
		for "historic" reasons. when acting as a list of eval results.
		during execution, results of evaluation of every node is appended,
		so there is a history available.
		current value is the last one.
		we might split this out into something like EvalResultsList
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
		#constants should call this..but if they are in a Parser, isconst wont propagate yet
		assert(isinstance(x, Node))
		if len(self) > 0:
			self[0] = x
		else:
			super(val, self).append(x)
		return x
	"""

	def eq_by_value(a, b):
		if len(a.items) != len(b.items):
			return False
		#otherwise..
		for i,v in enumerate(a.items):
			if not v.eq_by_value_and_python_class(b.items[i]):
				return False
		return True

class Statements(List):
	def __init__(s):
		super(Statements, s).__init__()
		s.view_mode = Collapsible.vm_multiline

	@classmethod
	def fresh(cls, decl=None):
		r = cls()
		r.newline()
		return r

	@property
	def item_type(self):
		return B.statement

	@staticmethod
	def match(text):
		return None

	def render_items(self):
		r = []
		for item in self.items:
			r += [ElementTag(item)]
			if self.view_mode == 2:
				r+= ['\n']
			else:
				r+= [TextTag(', ')]
			#we will have to work towards having this kind of syntax
			#defined declaratively so Parser can deal with it
		r += []
		return r

	def run(self):
		[i.eval() for i in self.items]
		return Text("it ran.")

	def _eval(self):
		results = [i.eval() for i in self.items]
		if len(results) == 0:
			return NoValue()
		else:
			return results[-1]

	#@property
	#def parsed(self):#i wonder if this is wise #nope, it wasnt
	#	r = Statements()
	#	r.parent = self###
	#	r.items = [i.parsed for i in self.items]
	#	#r.fix_parents()#fuck fuck fuck
	#	return r
	#war


"""
class SortedView():
	S_orig = 0
	S_alpha_type_betically_with_flattened_classes?

	@property
	def source(s):
		return (s.parent. #module
				ch.statements.parsed.items)

"""




class NoValue(Node):
	def __init__(self):
		super(NoValue, self).__init__()
	def render(self):
		return [TextTag('void')]
	def to_python_str(self):
		return "no value"
	def eq_by_value(a, b):
		return True

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

class WidgetedValue(WidgetedValuePersistenceStuff, Node):
	"""basic one-widget value"""
	is_const = True#this doesnt propagate to Parser yet, but anyway, this node always evaluates to the same value
	#during a program run. guess its waiting for type inference or something
	def __init__(self):
		super(WidgetedValue, self).__init__()	

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
		return [MemberTag('widget')]

	def to_python_str(self):
		return str(self.pyval)

	def copy(s):
		return s.__class__(s.pyval)

	def eq_by_value(a,b):
		return a.pyval == b.pyval

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.pyval)+"')"

class Number(WidgetedValue):
	easily_instantiable = True
	def __init__(self, value="0"):
		super(Number, self).__init__()
		self.widget = widgets.Number(self, value)
		self.widget.brackets = ('','')

	@classmethod
	def register_class_symbol(cls):
		log("registering number grammar")
		digit = m.symbol('digit')
		digits = m.symbol('digits')
		for i in [chr(j) for j in range(ord('0'), ord('9')+1)]:
			m.rule(i + "_is_a_digit",digit, m.known_char(i))

		m.sequence('digits_is_sequence_of_digit', digits, digit, join)
		r = m.symbol('number')
		m.rule('number_is_digits', r, digits, (ident, cls))
		return r

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
	easily_instantiable = True
	def __init__(self, value="", debug_note=""):
		super(Text, self).__init__()
		self.widget = widgets.Text(self, value)
		self.brackets_color = colors.text_brackets
		self.brackets = ('[',']')
		self.debug_note = debug_note

	@classmethod
	def register_class_symbol(cls):
		log("registering text grammar")
		double_slash = m.known_string('//')
		slashed_end =  m.known_string('/]')
		body_part = m.symbol('body_part')
		m.rule('string_body_part_is_double_slash', body_part, double_slash)
		m.rule('string_body_part_is_slashed_end', body_part, slashed_end)
		m.rule('string_body_part_is_nonspecial_char', body_part, m.syms.nonspecial_char)
		m.rule('string_body_part_is_known_char', body_part, m.syms.known_char)
		body = m.symbol('body')
		m.sequence('string_body is seq of body part', body, body_part, join)
		text = m.symbol('Text')
		opening =  m.known_char('[')
		closing =  m.known_char(']')
		m.rule('Text_is_[body]', text, [opening, body, closing], cls.from_parse)
		return text

	@classmethod
	def from_parse(cls, args):
		return cls(args[1])

	#def render(self):
	#	return self.widget.render()

	def _eval(self):
		return Text(self.pyval)

	@staticmethod
	def match(text):
		return 100


class Root(Dict):
	def __init__(self):
		super(Root, self).__init__()
		self.parent = None
		self.decl = None
		self.delayed_cursor_move = 0
		#the frontend moves the cursor by this many chars after a render()
		## The reason is for example a textbox recieves a keyboard event,
		## appends a character to its contents, and wants to move the cursor,
		## but before re-rendering, it might move it beyond the end of file
		self.indent_length = 4 #not really used but would be nice to have it variable
		self.changed = True

	@property
	def delayed_cursor_move(s):
		return s._delayed_cursor_move
	@delayed_cursor_move.setter
	def delayed_cursor_move(s, x):
		log ("setting delayed_cursor_move to %s"%(x,))
		s._delayed_cursor_move = x

	def render(self):
		#there has to be some default color for everything, the rendering routine looks for it..
		return [ColorTag(colors.fg)] + self.render_items() + [EndTag()]

	def delete_child(self, child):
		log("I'm sorry Dave, I'm afraid I can't do that.")

	def delete_self(self):
		log("I'm sorry Dave, I'm afraid I can't do that ")

	#def okay(s):
	#	recursively check parents?

	def scope(self):
		we_should_never_get_here()
		#crude, but for now..




class Module(Syntaxed):
	"""module or program"""
	def __init__(self, kids):
		super(Module, self).__init__(kids)
		#self.sortedview = SortableStatements(self)

	def add(self, item):
		self.ch.statements.add(item)

	def __getitem__(self, i):
		return self.ch.statements[i]

	def __setitem__(self, i, v):
		self.ch.statements[i] = v

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

	def reload(s):
		log(b_lemon_load_file(s.root, 'test_save.lemon.json'))
		return CHANGED

	def run(s):
		log(s.run())
		return CHANGED


	def save(self):
		#import yaml
		#s = yaml.dump(self.serialize(), indent = 4)
		#open('test_save.lemon', "w").write(s)
		#log(s)
		#todo easy: find a json module that would preserve odict ordering (or hjson)
		import json
		s = json.dumps(self.serialize(), indent = 4)
		open('test_save.lemon.json', "w").write(s)
		log(s)
		#except Exception as e:
		#	log(e)
		#	raise e
		return CHANGED

	def scope(self):

		if self != self.root["builtins"]:
			return self.root["builtins"].ch.statements.parsed
		else:
			return [] #nothing above but Root


# endregion

# region nodecls and stuff

class Ref(RefPersistenceStuff, Node):
	"""points to another node.
	if a node already has a parent, you just want to point to it, not own it"""
	#todo: separate typeref and ref?..varref..?
	def __init__(self, target):
		super(Ref, self).__init__()
		self.target = target

	@classmethod
	def register_class_symbol(cls):
		r = m.symbol('ref')

		for i in m.scope:
			if is_type(i):#todo: not just types but also functions and..?..
				rendering = "*" + i.name
				debug_name = "ref to"+str(i)
				sym = m.symbol(debug_name)
				m.rule(debug_name + "is a ref", r, sym)
				m.rule(debug_name, sym, m.known_string(rendering), cls.from_parse)

		return r

	@classmethod
	def from_parse(cls, x):
		log(x)

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
	def eq_by_value(a, b):
			if a.target == b.target:
				log("saying %s equals %s"%(a,b))
				return True
	def copy(s):
		return Ref(s.target)


class VarRef(VarRefPersistenceStuff, Node):
	def __init__(self, target):
		super(VarRef, self).__init__()
		self.target = target
		assert isinstance(target, (UntypedVar, TypedParameter))
		log("varref target:"+str(target))

	def render(self):
		return [TextTag('$'), ArrowTag(self.target), TextTag(self.name)]

	@property
	def name(self):
		return self.target.name

	def _eval(s):
		#it is already has a value
		return s.target.runtime.value.val

class Exp(Node):
	"""used to specify that an expression (something that evaluates to, at runtime) of
	some type, as opposed to a node of that type, is expected"""
	def __init__(self, type):
		super(Exp, self).__init__()
		self.type = type

	def render(self):
		return [MemberTag("type"), TextTag('expr')]

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
		instance_class.decl = Ref(self)
		self.decl = None
		self.example = None

	def register_symbol(s):
		s._symbol = s.instance_class.register_class_symbol()

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
		return self.instance_class.__name__.lower()

	def instantiate(self, kids):
		return self.instance_class(kids)

	def inst_fresh(self, decl=None):
		""" fresh creates default children"""
		return self.instance_class.fresh(decl)

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
	help = ["points to another node, like using an identifier. Used only for pointing to types."]
	def __init__(self):
		super(TypeNodecl, self).__init__(Ref)

	def palette(self, scope, text, node):
		nodecls = [x for x in scope if isinstance(x, (NodeclBase))]
		return [ParserMenuItem(Ref(x)) for x in nodecls]

	def make_example(s):
		return Ref(B.module)

class VarRefNodecl(NodeclBase):
	help=["points to a variable"]
	def make_example(s):
		item = B.untypedvar.instantiate({'name':Text("example variable")})
		items = list_of('text').inst_fresh()
		items.items = [Text(x) for x in ['a','b','c']]
		items.view_mode = 1
		p = FunctionCall(B.print)
		p.args['expression'] = VarRef(item)
		body = B.statements.inst_fresh()
		body.items = [p]#, Annotation(p, "this")]
		return For({'item': item,
					'items': items,
					'body': body})

	def __init__(self):
		super(VarRefNodecl, self).__init__(VarRef)


	def palette(self, scope, text, node):
		r = []
		for x in node.vardecls_in_scope:
			assert isinstance(x, (UntypedVar, TypedParameter))
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
				if isinstance(yc, (UntypedVar, TypedParameter)):
					#log("vardecl:"+str(yc))
					r += [ParserMenuItem(VarRef(yc))]
		#log (str(scope)+"varrefs:"+str(r))
		return r
"""
class ExpNodecl(NodeclBase):
	def __init__(self):
		super(ExpNodecl, self).__init__(Exp)

	def palette(self, scope, text, node):
		nodecls = [x for x in scope if isinstance(x, (NodeclBase))]
		return [ParserMenuItem(Exp(x)) for x in nodecls]

class Nodecl(NodeclBase):
	"""for simple nodes (Number, Text, Bool)"""
	def __init__(self, instance_class):
		super(Nodecl, self).__init__(instance_class)
		instance_class.decl = Ref(self)
		#print("building in",self.name)
		#build_in(self, self.name)
		#instance_class.name = self.name

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
	A Nodecl for a class derived from Syntaxed.
	instance_slots holds types of children, not Ref'ed.
	 children themselves are either Refs (pointing to other nodes),
	 or owned nodes (their .parent points to us)
	"""
	def __init__(self, instance_class, instance_syntaxes, instance_slots):
		super(SyntaxedNodecl , self).__init__(instance_class)
		self.instance_slots = dict([(k, B[i] if isinstance(i, unicode) else i) for k,i in iteritems(instance_slots)])
		if isinstance(instance_syntaxes[0], list):
			self.instance_syntaxes = instance_syntaxes
		else:
			self.instance_syntaxes = [instance_syntaxes]
		self.example = None

	def make_example(s):
			return s.inst_fresh()



class ParametricTypeBase(Syntaxed):
	pass

class ParametricType(ParametricTypeBase):
	"""like..list of <type>, the <type> will be a child of this node.
	 ParametricType is instantiated by ParametricNodecl """
	def __init__(self, children, decl):
		self.decl = decl
		self.instance_class = self.decl.value_class
		super(ParametricType, self).__init__(children)

	@property
	def slots(self):
		return self.decl.type_slots

	@property
	def syntaxes(self):
		return [self.decl.type_syntax]

	def inst_fresh(self, decl=None):
		"""create new List or Dict"""
		if not decl:
			decl = self
		return self.decl.value_class.fresh(Ref(decl))

	@classmethod
	def fresh(cls, decl):
		"""create new parametric type"""
		return cls(cls.create_kids(decl.type_slots), decl)

	@property
	def name(self):
		return "parametric type (probably a <list of something> type)"
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
	def __init__(self, value_class, type_syntax, type_slots):
		super(ParametricNodecl, self).__init__(ParametricType)
		self.type_slots = type_slots
		self.type_syntax = type_syntax
		self.value_class = value_class

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
		text = self.decl.ch.options[self.value].parsed
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
	def __init__(self, children):
		self.instance_class = EnumVal
		super(EnumType, self).__init__(children)
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

class SyntacticCategory(Syntaxed):
	help=['this is a syntactical category(?) of nodes, used for "statement" and "expression"']

	def __init__(self, children):
		super(SyntacticCategory, self).__init__(children)

	def register_symbol(s):
		s._symbol = lhs = m.symbol(
			repr(s))

class WorksAs(Syntaxed):
	help=["declares a subtype relation between two existing types"]
	def __init__(self, children):
		super(WorksAs, self).__init__(children)

	def forget_symbols(s):
		super(WorksAs, s).forget_symbols()
		s._rule = None

	def register_symbol(s):
		if s._rule != None:
			return
		lhs = s.ch.sup.target.symbol
		rhs = s.ch.sub.target.symbol
		if args.log_parsing:
			log('%s %s %s %s %s'%(s, s.ch.sup, s.ch.sub, lhs, rhs))
		if lhs != None and rhs != None:
			r = m.rule(str(s), lhs, rhs)
			s._rule = r

	@classmethod
	def b(cls, sub, sup):
		"""building-in helper"""
		return cls({'sub': Ref(B[sub]), 'sup': Ref(B[sup])})

class Definition(Syntaxed):
	"""should have type functionality (work as a type)"""
	help=['used just for types, currently.']
	def __init__(self, children):
		super(Definition, self).__init__(children)

	def inst_fresh(self):
		return self.ch.type.inst_fresh(self)

	def palette(self, scope, text, node):
		return self.ch.type.palette(scope, text, None)

	@property
	def type(s):
		return s.ch.type.parsed

class Union(Syntaxed):
	help=['an union of types means that any type will satisfy']
	def __init__(self, children):
		super(Union, self).__init__(children)

# endregion

class ListOfAnything(ParametricType):

	def palette(self, scope, text, node):
		#log(self.ch._dict)
		i = self.inst_fresh()
		i.view_mode = 1
		i.newline()
		return [ParserMenuItem(i)]
	def works_as(self, type):
		return True

class UntypedVar(Syntaxed):
	easily_instantiable = True
	def __init__(self, children):
		super(UntypedVar, self).__init__(children)


class For(Syntaxed):
	def __init__(self, children):
		super(For, self).__init__(children)

	@property
	def vardecls(s):
		return [s.ch.item]

	def _eval(s):
		itemvar = s.ch.item.parsed
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

class VarlessFor(Syntaxed):
	def __init__(self, children):
		self.it = B.untypedvar.inst_fresh()
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


class If(Syntaxed):
	def __init__(self, children):
		super(If, self).__init__(children)

	def _eval(s):
		c = s.ch.condition.eval()
		#lets just do it by hand here..
		if c.decl != B.bool:
			return Banana("%s is of type %s, i cant branch with that"%(c, c.decl))
		if c.pyval == 1:
			log("condition true")
			return s.ch.statements.eval()
		else:
			log("condition false")
			return NoValue()

class Else(Syntaxed):
	"""a dangling else...dang!"""
	def __init__(self, children):
		super(Else, self).__init__(children)

	def _eval(s):
		if isinstance(s.parent, Parser):
			parent = s.parent.parent
			child = s.parent
		else:
			parent = s.parent
			child = s
		if not isinstance(parent, Statements):
			return Banana("parent is not Statements")
		above = parent.above(child)
		if not len(above):
			return Banana("no nodes above me, much less an If")
		a = above[-1].parsed
		if not isinstance(a, If):
			return Banana("whats above me is not an If and that makes me cry")
		c = a.ch.condition
		if not 'value' in c.runtime._dict:
			return Banana("the node above me wasnt evaluated, how am i to know if i should run?")
		if c.runtime.value.val.pyval == 0:
			return s.ch.statements.eval()
		else:
			#log(repr(c.runtime.value.val.pyval))
			#return NoValue()
			return a.runtime.value.val


"""
class Filter(Syntaxed):
	def __init__(self, kids):
		super(Filter, self).__init__(kids)
"""
# endregion

# region parser

class ParserBase(Node):

	"""
	Parser node

	todo:hack it so that the first node, when a second node is added, is set as the
	leftmost child of the second node..or maybe not..dunno
	"""

	def __init__(self):
		super(ParserBase, self).__init__()
		self.items = NotifyingList()
		self.items.append(widgets.Text(self,"x"))
		self.decl = None
		self.on_edit = Signal()
		self.brackets_color = colors.compiler_brackets
		self.brackets = ('{', '}')
		self.reregister = False

	@property
	def items(s):
		return s._items

	@items.setter
	def items(s, x):
		s._items = NotifyingList(x)
		s._items.register_callback(s.items_changed)

	def items_changed(s):
		#s.root.rerender = s.reparse = True
		pass

		#hmm,,...

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
		assert isinstance(item, (widgets.Text, Node) ), repr(item)
		#if isinstance(item, Node):
		item.parent = self


	def even_out(inp):
		"""
		after each change, we go thru items:
			input is a list of Texts and Nodes
			if there are two Texts next to each other, concat them
			if there are two Nodes next to each other, put a Text between them
			ensure there is a Text at the beginning and at the end
		"""

		#find adjacent items of same type
		def find_same_type_pair(items, type):
			for index, i in enumerate(items[:-1]):
				if isinstance(i, type) and isinstance(items[index+1], type):
					return index

		#find adjacent Texts and join them
		while True:
			index = find_same_type_pair(inp, widgets.Text)
			if index == None: break
			inp[index] = widgets.Text(inp[index].value + inp[index+1].value)
			del inp[index+1]

		#find adjacent Nodes and put an empty Text between
		while True:
			index = find_same_type_pair(inp, Node)
			if index == None: break
			inp.insert(index+1, widgets.Text())

		#ensure Text at beginning and end
		if type(inp[0]) != widgets.Text: inp.insert(0, widgets.Text())
		if type(inp[-1]) != widgets.Text: inp.append(widgets.Text())




	"""
		li = event.any_atts.get('list_item')
		if li:
			if li[0] == self:
				return li[1]
	"""


	"""if there is a node followed by text and backspace is pressed between"""



	def render(self):
		if len(self.items) == 0: # no items, show the gray type hint
			return self.empty_render()

		r = []
		for i, item in enumerate(self.items):
			yield [
				AttTag(Att.item_index, (self, i)),
				ElementTag(item),
				EndTag()]

		return r
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

	def mine(s, atts):
		"""
		atts are the attributs of the char under cursor,
		passed to us with an event. figure out if and which of our items
		is under cursor
		"""

		if len(s.items) == 0:
			return None # no items in me

		if "compiler body" in atts and atts["compiler body"] == s:
			ci = atts["compiler item"]
			log("compiler item", ci)
			if "opening bracket" in atts:
				if ci == 0:
					return 0
				else:
					return ci - 1
			else:
				return ci
		else:
			#we should only get an event if cursor is on us, so this can only
			#be our closing bracket, all the rest is covered by "compiler body".
			return len(s.items)-1 #first from end
			#mm ok so this returns the first item from end, and that seems right
			#and if thats a node, we start a new string before it..hmm
			#i think we should return a tuple when the cursor is between two
			#items and deal with that in on_keypress


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
	
	"""todo:write tests and debug this monstrosity.
	#especially typing at the end of Parser, after a node, puts text in wrong place
	i know it wont be quite what we
	want anyway, but its a start and can be played around with.
	then think about text with metadata or something."""

	def menu_item_selected(s, item, atts=None):
		char_index = 0
		if atts == None:
			i = 0
		else:
			i = s.mine(atts)
			if isinstance(i, unicode):
				if "compiler item char" in atts:
					char_index = atts["compiler item char"]
				else:
					char_index = len(i)

		return s.menu_item_selected_for_child(item, i, char_index)

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
				#...
			s.root.delayed_cursor_move = (fch,)
		#todo
		#elif isinstance(node, FunctionCall):
		#	if len(node.args) > 0:
		#		s.root.post_render_move_caret = node.args[0]
		elif isinstance(node, WidgetedValue):
			if len(node.widget.text) > 0:
				s.root.delayed_cursor_move += 2
				#another hacky option: post_render_move_caret_after
				#nonhacky option: render out a tag acting as an anchor to move the cursor to
				#this would be also useful above
		elif isinstance(node, List):
			if len(node.items) > 0:
				s.root.delayed_cursor_move = (node.items[0],)
		#todo etc. make the cursor move naturally

	def delete_child(s, child):
		log("del")
		del s.items[s.items.index(child)]

	def replace_child(s, child, new):
		s.items[s.items.index(child)] = new
		s.fix_parents()

class Parser(ParserPersistenceStuff, ParserBase):
	"""the awkward input node AKA the Beast.
	im thinking about rewriting the items into nodes again.
	 this time with smarter cursor movement.
	"""
	def __init__(self, slot):
		super(Parser, self).__init__()
		self.slot = slot

	def copy(s):
		r = Parser(s.slot)
		for i in s.items:
			if isinstance(i, unicode):
				x = i
			else:
				x = i.copy()
			r.add(x)
		return r

	@property
	def type(s):
		return s.parent.slots[s.slot]

	def empty_render(s):
		return [ColorTag(colors.compiler_hint), TextTag('('+s.type.name+')'), EndTag()]

	@property
	def parsed(self):
		#default result:		#raise an exception?
		r = Bananas(self.items)

		if len(self.items) == 1:
			i0 = self.items[0]
			if isinstance(i0, Node):
				r = i0
			else: #widgets.Text
				#demodemodemo
				type = self.type
				if isinstance(self.type, Exp):
					type = self.type.type
				if isinstance(type, Ref):
					type = type.target

				i0 = i0.text
#				if type == b['number']:
				if Number.match(i0):
					r = Number(i0)
						#log("parsed it to Number")

				if type == B.text:
					r = Text(i0)


		r.parent = self
		#log(self.items, "=>", r)
		return r

	def _eval(self):
		return self.parsed.eval()

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
	def menu_item_selected_for_child(self, item, child_index, atts):
		if isinstance(item, (LeshMenuItem)):
			return False#hack
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


	def parse(s, scope):
		if not marpa:
			return []
		if len(s.items) != 1:
			return []
		it = s.items[0]
		if isinstance(it, Node):
			return []

		log("SETUP GRAMMA")
		setup_grammar(s.root, scope)
		raw = it

		r = []

		parse_result = parse(it)
		if parse_result  == None:
			return []

		"""maybe we want to only make the start_is_something rules
		when that something cant be reached from Statement thru WorksAs..
		lets just prune the duplicate results for now"""
		"""
		parse_result = list(parse_result)
		r2 = parse_result[:]
		nope = []
		for i,v in enumerate(parse_result):
			for susp in parse_result:
				if susp != v and v.eq_by_value(susp):
					nope.append(v)
		parse_result = [i for i in parse_result if not i in nope]
		"""#i dont feel like implementing eq_by_value for everything now

		for i in parse_result:
			r.append(ParserMenuItem(i, 333))

		return r

	def create_palette(self, atts):
		return self.palette_for_item(self.my_item(atts))

	def palette_for_item(self, i=0, debug = False):

		if i == None:
			if len(self.items) == 0:
				text = ""
			else:
				assert False
		else:
			if isinstance(self.items[i], Node):
				text = ""
			else:
				text = self.items[i]

		scope = self.scope()

		menu = flatten([x.palette(scope, text, self) for x in scope])


	def score_palette(items, text, type):
		matchf = fuzz.token_set_ratio#partial_ratio

		if isinstance(type, Exp):
			type = type.type

		def score_item(item):
			v = item.value
			try:
				item.scores.name = matchf(v.name, text), v.name #0-100
			except AttributeError as e:
				# no name
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

		map(score_item, items)

		menu.sort(key=lambda i: -i.score)

		#if debug:
		#	log('MENU FOR:',text,"type:",self.type)
		#	[log(str(i.value.__class__.__name__) + str(i.scores._dict)) for i in menu]

		return menu

	def long__repr__(s):
		return object.__repr__(s) + "(for type '"+str(s.type)+"')"

class ParserMenuItem(MenuItem):
	def __init__(self, value, score = 0):
		super(ParserMenuItem, self).__init__()
		self.value = value
		value.parent = self
		self.scores = Dotdict()
		if score != 0:  self.scores._ = score
		self.brackets_color = colors.parser_menu_item_brackets

	@property
	def score(s):
		#print s.scores._dict
		return sum([i if not isinstance(i, tuple) else i[0] for i in itervalues(s.scores._dict)])

	def tags(self):
		return [MemberTag('value'), ColorTag(colors.menu_item_extra_info), " - "+str(self.value.__class__.__name__)+' ('+str(self.score)+')', EndTag()]

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.value)+"')"

class DefaultParserMenuItem(MenuItem):
	def __init__(self, text):
		super(DefaultParserMenuItem, self).__init__()
		self.text = text
		self.brackets_color = colors.default_parser_menu_item_brackets


	def tags(self):
		return [TextTag(self.text)]
# endregion

# region functions


"""
# todo function arguments:
# todo optional types
# todo: show and hide argument names. syntaxed?
"""




class FunctionParameterBase(Syntaxed):
	pass

class TypedParameter(FunctionParameterBase):
	"""a parameter to a function, with a name and a type specified"""
	def __init__(self, children):
		super(TypedParameter, self).__init__(children)
	@property
	def type(s):
		return s.ch.type.parsed


class UnevaluatedParameter(FunctionParameterBase):
	"""this argument will be passed to the called function as is, without evaluation"""
	def __init__(self, children):
		super(UnevaluatedParameter, self).__init__(children)
	@property
	def type(s):
		return s.ch.argument.type

class FunctionDefinitionBase(Syntaxed):

	def __init__(self, children):
		super(FunctionDefinitionBase, self).__init__(children)

	def register_symbol(s):

		rhs = []
		for i in s.sig:
			if type(i) == Text:
				a = m.known_string(i.pyval)
			elif isinstance(i, TypedParameter):
				#TypedParameter means its supposed to be an expression
				a = B.expression.symbol
				assert a,  i
			elif isinstance(i, UnevaluatedArgument):
				a = deref_decl(i.type).class_symbol
				assert a,  i
			assert a,  i
			rhs.append(a)
			rhs.append(m.syms.maybe_spaces)
		if args.log_parsing:
			log('rhs:%s'%rhs)
			debugname = "call of "+repr(s)
		else:
			debugname=""
		s._symbol = m.symbol(debugname)
		m.rule(debugname, s._symbol, rhs, s.marpa_create_call)
		m.rule("call is "+debugname, B.call.symbol, s._symbol)

	def marpa_create_call(s, args):
		'takes an array of argument nodes, presumably'
		for i in args:
			if i != None: # a separator
				assert isinstance(i, (unicode, Node)),  i
		args = [i for i in args if isinstance(i, Node)]

		assert len(args) == len(s.params)

		r = FunctionCall(s)

		for k,v in iteritems(s.params):
			r.args[k] = args.pop(0)

		r.fix_parents()

		return r


	@property
	def params(self):
		r = odict([(i.name, i) for i in self.sig if isinstance(i, FunctionParameterBase)])
		#for i in itervalues(r):
		#	assert(i.parent)
		return r

	@property
	def sig(self):
		sig = self.ch.sig.parsed
		#check..
		for i in sig.items:
			assert(i.parent)

		#check..
		if not isinstance(sig, List):
			log("sig did not parse to list but to ", repr(sig))
			r = [Text("function's sig is not a List")]
		else:
			r = [i.parsed for i in sig.items]

		#some checks..
		for i in r:
			if not isinstance(i, (UnevaluatedParameter, TypedParameter, Text)):
				r = [Text("bad item in sig:"+repr(i))]
				break

		#more checks..
		rr = []
		for i in r:
			if isinstance(i, (UnevaluatedParameter, TypedParameter)):
				if not is_type(i.type):
					rr.append(Text(" bad type "))
				else:
					rr.append(i)
			else:
				rr.append(i)

		return rr

	@property

	def vardecls(s):
		log(s.params)
		r = [i if isinstance(i, TypedParameter) else i.ch.argument for i in itervalues(s.params)]
		#print ">>>>>>>>>>>", r
		return r

	def typecheck(self, args):
		for name, arg in iteritems(args):
			#if not arg.type.eq(self.arg_types[i])...
			if not hasattr(arg, 'decl'):
				return Banana(str(arg) +" ?! ")
			expected_type = self.params[name].type
			if isinstance(expected_type, Ref) and hasattr(arg, 'decl') and isinstance(arg.decl, Ref):
				if not arg.decl.target == expected_type.target:
					log("well this is maybe bad, decl %s of %s != %s" % (arg.decl, arg, expected_type))
					return Banana(str(arg.decl.name) +" != "+str(expected_type.name))
		return True


	def call(self, args):
		"""common for all function definitions"""
		evaluated_args = {}
		for name, arg in iteritems(args):
			if not isinstance(arg, UnevaluatedParameter):
				evaluated_args[name] = arg.eval()
			else:
				evaluated_args[name] = arg.parsed
		log("evaluated_args:", [i.long__repr__() for i in itervalues(evaluated_args)])

		assert(len(evaluated_args) == len(self.params))
		r = self._call(evaluated_args )
		assert isinstance(r, Node), "_call returned "+str(r)
		return r

	def _eval(s):
		"""this is when the declaration is evaluated, not when we are called"""
		return Text("ok, function was declared.")
	"""
	def _unresolvize(s):
		#return dict(super(FunctionDefinitionBase, self).un,
		return {
		        'function':True,
		        'sig':[i.serialize() for i in s.sig],
       			'ret': s.ret,
		}
	"""

	def palette(self, scope, text, node):
		return [ParserMenuItem(FunctionCall(self))]


"""for function overloading, we could have a node that would be a "Variant" of
	an original function, with different arguments.
"""


class FunctionDefinition(FunctionDefinitionPersistenceStuff, FunctionDefinitionBase):
	"""function definition in the lemon language"""
	def __init__(self, children):
		super(FunctionDefinition, self).__init__(children)

	def _call(self, call_args):
		self.copy_args(call_args)
		#log(call_args)
		return self.ch.body.eval()

	def copy_args(self, call_args):
		for k,v in iteritems(call_args):
			assert isinstance(k, unicode)
			assert isinstance(v, Node)
			self.params[k].append_value(v.copy())


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
	"""dumb and most powerful builtin function kind,
	leaves type-checking to the function"""
	def __init__(self, children):
		self._name = 777
		self.fun = 777
		super(BuiltinFunctionDecl, self).__init__(children)

	@staticmethod
	def create(name, fun, sig):
		x = BuiltinFunctionDecl.fresh()
		x._name = name
		build_in(x, name)
		x.ch.name.widget.value = name
		x.fun = fun
		x.ch.sig = B.function_signature_list.inst_fresh()
		x.ch.sig.items = sig
		for i in sig:
			assert(isinstance(i, (Text, TypedParameter)))
		x.fix_parents()
		B[name] = x

	def _call(self, args):
		return self.fun(args)
		# todo use named *args i guess

	@property
	def name(s):
		return s._name

	#def palette(self, scope, text, node):
	#	return []

	def _unresolvize(s):
		return dict(super(BuiltinFunctionDecl, s)._unresolvize(),
		    note = s.note,
		    name = s.name,
		    #fun = s.fun,
		)




class BuiltinPythonFunctionDecl(BuiltinFunctionDecl):
	"""checks args,
	converts to python values,
	calls python function,
	converts to lemon value.
	This can call any lemon-unaware python function,
	but has to be set up from within python code.
	this is just a step from user-addable python function
	"""
	def __init__(self, children):
		self.ret= 777
		self.note = 777
		self.pass_root = False # pass root as first argument to the called python function? For internal lemon functions, obviously
		super(BuiltinPythonFunctionDecl, self).__init__(children)

	@staticmethod
	#todo:refactor to BuiltinFunctionDecl.create
	#why do we have 2 kinds of names here?
	def create(fun, sig, ret, name, note):
		x = BuiltinPythonFunctionDecl.fresh()
		x._name = name
		build_in(x)
		x.ch.name.widget.value = fun.__name__
		x.fun = fun
		x.ch.sig = B.function_signature_list.inst_fresh()
		x.ch.sig.items = sig
		x.ch.sig.fix_parents()
		for i in sig:
			assert(isinstance(i, (Text, TypedParameter)))
		x.ch.ret = ret
		x.note = note
		x.ret = ret
		x.fix_parents()
		return x

	def _call(self, args):
		#translate args to python values, call python function
		checker_result = self.typecheck(args)
		if checker_result != True:
			return checker_result
		pyargs = []
		if self.pass_root:
			pyargs.append(self.root)
		for i in self.sig:
			if not isinstance(i, Text): #typed or untyped argument..
				pyargs.append(args[i.name].pyval)
		python_result = self.fun(*pyargs)
		lemon_result = self.ret.inst_fresh()
		lemon_result.pyval = python_result #todo implement pyval assignments
		return lemon_result

	#def palette(self, scope, text, node):
	#	return []



class FunctionCall(FunctionCallPersistenceStuff, Node):
	def __init__(self, target):
		super(FunctionCall, self).__init__()
		assert isinstance(target, FunctionDefinitionBase)
		self.target = target
		for i in itervalues(self.target.params):
			assert not isinstance(i.type, Parser), "%s to target %s is a dumbo" % (self, self.target)
		self.args = dict([(name, Parser(name)) for name, v in iteritems(self.target.params)]) #this should go to fresh(?)
		self.fix_parents()

	@classmethod
	def register_class_symbol(cls):
		return m.symbol("function_call")

	@property
	def slots(s):
		return s.target.params

	def fix_parents(s):
		s._fix_parents(itervalues(s.args))

	def _eval(s):
		args = s.args#[i.compiled for i in s.args]
		log("function call args:"+str(args))
		return s.target.call(args)

	def delete_child(s, child):
		assert(child in s.args)
		for k,v in iteritems(s.args):
			if v == child:
				s.replace_child(child, Parser(k))
				break

	def replace_child(self, child, new):
		assert(child in self.args)
		self.args[self.args.index(child)] = new
		new.parent = self

	def render(self):
		sig = self.target.sig
		assert isinstance(sig, list)
		assert len(self.args) == len(self.target.params),\
			(len(self.args),len(self.target.params),self.args, self.target.params,self, self.target)
		r = []
		for v in sig:
			if isinstance(v, Text):
				r += [TextTag(v.pyval)]
			elif isinstance(v, TypedParameter):
				r += [ElementTag(self.args[v.name])]
			else:
				raise Exception("item in function signature is"+str(v))
		return r

	@property
	def name(s):
		return s.target.name

	def _flatten(self):
		return [self] + flatten([v.flatten() for v in itervalues(self.args)])


class FunctionCallNodecl(NodeclBase):
	"""a type of FunctionCall nodes,
	offers function calls thru palette()"""
	def __init__(self):
		super(FunctionCallNodecl, self).__init__(FunctionCall)
	def palette(self, scope, text, node):
		#override NodeclBase palette() which returns a menuitem with a fresh() instance_class,
		#FunctionCall cant be instantiated without a target.
		return []
		#the stuff below is now performed in FunctionDefinitionBase
#		decls = [x for x in scope if isinstance(x, (FunctionDefinitionBase))]
#		return [ParserMenuItem(FunctionCall(x)) for x in decls]



# endregion

# region misc nodes

def build_in_misc():
	class Note(Syntaxed):
		def __init__(self, children):
			self.text = widgets.Text(self, "")
			super(Note,self).__init__(children)

	build_in(SyntaxedNodecl(Note,
				   [["note: ", MemberTag("text")]],
				   {'text': Exp(B.text)}))


	class Annotation(Node):
		def __init__(self, target, text):
			self.text = text
			self.target = target
			super(Annotation,self).__init__()

		def render(s):
			return [ArrowTag(s.target), TextTag(s.text)]


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
				   {'text': Exp(B.text)})



	class ShellCommand(Syntaxed):
		info = ["runs a command with os.system"]
		def __init__(self, children):
			super(ShellCommand, self).__init__(children)

		def _eval(s):
			cmd = s.ch.command.eval()
			import os
			try:
				return Text(str(os.system(cmd.pyval)))
			except Exception as e:
				return Text(str(e))

	build_in(SyntaxedNodecl(ShellCommand,
				   [["bash:", ChildTag("command")]],
				   {'command': Exp(B.text)}))


	class FilesystemPath(Syntaxed):
		def __init__(self, children):
			self.status = widgets.Text(self, "(status)")
			self.status.color = colors.compiler_hint
			super(FilesystemPath, self).__init__(children)

		def _eval(s):
			p = s.ch.path.eval().pyval
			from os import path
			s.status.text = "(valid)" if path.exists(p) else "(invalid)"
			return Text(p)


	build_in(SyntaxedNodecl(FilesystemPath,
				   [[ChildTag("path")],
				    [ChildTag("path"), MemberTag("status")]],
				   {'path': Exp(B.text)}))

	def b_files_in_dir(dir):
		import os
		for x in os.walk(dir):
			return x[2]
		return []

	BuiltinPythonFunctionDecl.create(b_files_in_dir, [Text("files in"), text_arg()], list_of('text'), "list files in dir", "ls, dir")

	def b_lemon_load_file(root, name):
		try:
			log("loading "+name)
			try:
				#import yaml
				#input = yaml.load(open(name, "r").read())
				import json
				input = json.load(open(name, "r"))
			except Exception as e:
				return str(e)

			#root["loaded program"] = b['module'].inst_fresh() # this is needed so that the module correctly limits scope resolving during deserialization
			#root["loaded program"].parent = root
			root["loaded program"] = deserialize(input, root["loaded program"])
			root.fix_parents()
			for i in root["loaded program"].flatten():
				if isinstance(i, Serialized):
					i.unserialize()
			root.fix_parents()
		except Exception as e:
			raise

		return name + " loaded ok"

	def load_module(file, placeholder):
		log("loading "+file)
		input = json.load(open(file, "r"))
		d = deserialize(input, placeholder)
		placeholder.parent.replace_child(d)
		d.fix_parents()
		for i in d.flatten():
			if isinstance(i, Serialized):
				i.unserialize()
			d.fix_parents()
		log("ok")

	BuiltinPythonFunctionDecl.create(
		b_lemon_load_file, [Text("load"), text_arg()], Ref(B.text), "load file", "open").pass_root = True

	"""
	def editor_load_file(name):
		path = name.eval().text
	    log("loading", path)
		try:
			data = json.load(open(path, "r"))
			root = name.root #hack
			r.add(("loaded program", deserialize0(root, data)))
		except Exception as e:
			log(e)
	"""

	# endregion



def make_root():
	r = Root()

	build_in_editor_structure_nodes()
	build_in_lemon_language()

	r["intro"] = new_module()
	r["intro"].ch.statements.items = [
		Text("""

Welcome to lemon! Press F1 to cycle the sidebar!
the interface of lemon is currently implemented like this:
root is a dictionary with keys like "intro", "some program" etc.
it's values are mostly modules. modules can be collapsed and expanded and they
hold some code or other stuff in a Statements object. This is a text literal inside a module, too.

Lemon can't do much yet. You can add function calls and maybe define functions. If you are lucky,
ctrl-d will delete something. Inserting of nodes happens in the Parser node."""),
		#it looks like this:"""),
		#Parser(b['number']), todo:ParserWithType
		Text("If cursor is on a parser, a menu will appear in the sidebar. you can scroll and click it. have fun."),
		Text("todo: working editor, smarter menu, better parser, real language, fancy projections...;)")
	]

	
	r["intro"].ch.statements.view_mode=0
	#r.add(("lesh", Lesh()))
	r["some program"] = B.module.inst_fresh()
	r["some program"].ch.statements.newline()
	#r['some program'].ch.statements.items[1].add("12")
	#r["lemon console"] =b['module'].inst_fresh()
	r["loaded program"] = Text("placeholder 01")

	library = r["library"] = make_list('module')
	import glob
	for file in glob.glob("library/*.lemon.json"):
		placeholder = library.add(new_module())
		placeholder.ch.name.pyval = "placeholder for "+file
		load_module(file, placeholder)

	#todo: walk thru weakrefs to serialized, count successful deserializations, if > 0 repeat?




	r["builtins"] = new_module()
	r["builtins"].ch.statements.items = list(itervalues(B._dict))
	assert len(r["builtins"].ch.statements.items) == len(B) and len(B) > 0
	log("built in %s nodes",len(r["builtins"].ch.statements.items))
	r["builtins"].ch.statements.add(Text("---end of builtins---"))
	r["builtins"].ch.statements.view_mode = 2





	#r.add(("toolbar", toolbar.build()))

	#log(len(r.flatten()))
	#for i in r.flatten():
	#		assert isinstance(i, Root) or i.parent, i.long__repr__()
	#		if not i.parent:
	#			log(i.long__repr__())
	#log("--------------")
	#log(r["builtins"].ch.statements.items)
	#test_serialization(r)
	#log(b_lemon_load_file(r, 'test_save.lemon.json'))
	#log(len(r.flatten()))
	#log(r["builtins"].ch.statements.items)
	#import gc
	#log(gc.garbage)
	#gc.collect()
	#r["some program"].save()
	#log("ok")
	r.fix_parents()
	if __debug__:
		for i in r.flatten():
			if not isinstance(i, Root):
				assert i.parent,  i.long__repr__()
	return r


"""
decide if declarative nodes like SyntacticCategory and Definition should have
the name as a child node...it doesnt seem to make for a clear reading

#todo: node syntax is a list of ..
#node children types is a list of ..

todo:rename FunctionDefinition to Defun, FunctionCall to Call, maybe remove "Stuff"s
"""



def build_in_editor_structure_nodes():

	build_in(Nodecl(Text))
	build_in(TypeNodecl(), 'type')

	build_in(
	ParametricNodecl(List,
					 [TextTag("list of"), ChildTag("itemtype")],
					 {'itemtype': B.type}),'list')

	build_in(
		SyntaxedNodecl(SyntacticCategory,
			[TextTag("syntactic category:"), ChildTag("name")],
			{'name': 'text'}))

	build_in(SyntacticCategory({'name': Text("statement")}))

	build_in(Nodecl(Statements))

	build_in(
	SyntaxedNodecl(Module,
				   ["module", ChildTag("name"), 'from', ChildTag("file"), ":\n", ChildTag("statements"),  TextTag("end.")],
				   {'statements': B.statements,
				    'name': B.text,
				    'file': B.text
				    }))

def build_in_lemon_language():

	build_in(Text(
	"""We start by declaring the existence of some types (decls).
	Once declared, we can reference them from lemon objects.
	Internally, each declaration is a Nodecl object.
	The type name is usually a lowercased
	name of the python class that implements it."""))


	build_in(VarRefNodecl(), 'varref')

	build_in([Nodecl(x) for x in [Number, Banana, Bananas]])

	build_in(Nodecl(List), "list_literal")

	build_in([

	SyntaxedNodecl(WorksAs,
				   [ChildTag("sub"), TextTag("works as"), ChildTag("sup")],
				   {'sub': 'type', 'sup': 'type'}),
	SyntaxedNodecl(Definition,
				   [TextTag("define"), ChildTag("name"), TextTag("as"), ChildTag("type")], #expression?
				   {'name': 'text', 'type': 'type'}),

	SyntacticCategory({'name': Text("anything")}),
	SyntacticCategory({'name': Text("expression")})
	])

	build_in(WorksAs.b("statement", "anything"), False)
	build_in(WorksAs.b("expression", "statement"), False)
	build_in(WorksAs.b("number", "expression"), False)
	build_in(WorksAs.b("text", "expression"), False)

	build_in(
	ParametricNodecl(Dict,
					 [TextTag("dict from"), ChildTag("keytype"), TextTag("to"), ChildTag("valtype")],
					 {'keytype': B.type, 'valtype': B.type}), 'dict')

	build_in(WorksAs.b("list", "expression"), False)
	build_in(WorksAs.b("dict", "expression"), False)



	#build_in(ListOfAnything({'itemtype':b['anything']}, b['list']), 'list of anything')

	build_in(SyntaxedNodecl(EnumType,
				   ["enum", ChildTag("name"), ", options:", ChildTag("options")],
				   {'name': 'text',
				   'options': list_of('text')}))

	#Definition({'name': Text("bool"), 'type': EnumType({
	#	'name': Text("bool"),
	#	'options':b['enumtype'].instance_slots["options"].inst_fresh()})})
	build_in(EnumType({'name': Text("bool"),
		'options':B.enumtype.instance_slots["options"].inst_fresh()}), 'bool')

	B.bool.ch.options.items = [Text('false'), Text('true')]
	lemon_false, lemon_true = EnumVal(B.bool, 0), EnumVal(B.bool, 1)

	#Definition({'name': Text("statements"), 'type': b['list'].make_type({'itemtype': Ref(b['statement'])})})

	build_in(
		Definition(
			{'name': Text("list of types"),
			 'type': B.list.make_type(
				 {'itemtype': Ref(B.type)})}))

	build_in(SyntaxedNodecl(Union,
				   [TextTag("union of"), ChildTag("items")],
				   {'items': B.list.make_type({'itemtype': B.type})}))
				   #todo:should use the definition above instead

	B.union.notes="""should appear as "type or type or type", but a Syntaxed with a list is an easier implementation for now"""


	build_in(SyntaxedNodecl(UntypedVar,
				   [ChildTag("name")],
				   {'name': 'text'}))

	build_in(SyntaxedNodecl(For,
				   [TextTag("for"), ChildTag("item"), ("in"), ChildTag("items"),
				        ":\n", ChildTag("body")],
				   {'item': B.untypedvar,
				    'items': Exp(
					    B.list.make_type({
					        'itemtype': Ref(B.type)#?
					    })),
				   'body': B.statements}))


	build_in(SyntaxedNodecl(VarlessFor,
				   [TextTag("for"), ChildTag("items"),
				        ":\n", ChildTag("body")],
				   {'items': Exp(list_of('type')),
				   'body': B.statements}))


	build_in(SyntaxedNodecl(If,
				[
					[TextTag("if"), ChildTag("condition"), ":\n", ChildTag("statements")],

				],
				{'condition': Exp(B.bool),
				'statements': B.statements}))

	build_in(SyntaxedNodecl(Else,
				[
					[TextTag("else:"), ":\n", ChildTag("statements")],

				],
				{'statements': B.statements}))


	"""...notes: formatting: we can speculate that we will get to having a multiline parser,
	and that will allow for a more freestyle formatting...
	"""

	build_in(SyntaxedNodecl(TypedParameter,
				   [ChildTag("name"), TextTag("-"), ChildTag("type")],
				   {'name': 'text', 'type': 'type'}))


	builtin_unevaluatedparameter = build_in(SyntaxedNodecl(UnevaluatedParameter,
				   [TextTag("unevaluated"), ChildTag("argument")],
				   {'argument': 'typedparameter'}))



	#lets define a function signature type
	tmp = B.union.inst_fresh()
	tmp.ch["items"].add(Ref(B.text))
	tmp.ch["items"].add(Ref(B.typedparameter))
	tmp.ch["items"].add(Ref(builtin_unevaluatedparameter))
	build_in(Definition({'name': Text('function signature node'), 'type': tmp}))
	tmp = B.list.make_type({'itemtype': Ref(B.function_signature_node)})
	build_in(Definition({'name': Text('function signature list'), 'type':tmp}))
	#todo:refactor
	#and a custom node syntax type
	tmp = B.union.inst_fresh()
	tmp.ch["items"].add(Ref(B.text))
	tmp.ch["items"].add(Ref(B.type))
	build_in(Definition({'name': Text('custom syntax'), 'type': tmp}))
	tmp = B.list.make_type({'itemtype': Ref(B.custom_syntax)})
	build_in(Definition({'name': Text('custom syntax list'), 'type':tmp}))



	#tmp = b['list'].make_type({'itemtype': Ref(b['union of function signature item types'])})
	#tmp = b['list'].make_type({'itemtype': Ref(b['union of custom syntax item types'])})


	build_in(SyntaxedNodecl(FunctionDefinition,
				   [TextTag("deffun:"), ChildTag("sig"), TextTag(":\n"), ChildTag("body")],
					{'sig': B.function_signature_list,
					 'body': B.statements}))

	#user cant instantiate it, but we make a decl anyway,
	#because we need to display it, its in builtins,
	#its just like a normal function, FunctionCall can
	#find it there..
	build_in(SyntaxedNodecl(BuiltinFunctionDecl,
				   [TextTag("builtin function"), ChildTag("name"), TextTag(":"), ChildTag("sig")],
					{'sig': B.function_signature_list,
					 'name': B.text}))



	build_in(SyntaxedNodecl(BuiltinPythonFunctionDecl,
			[
			TextTag("builtin python function"), ChildTag("name"),
			TextTag("with signature"), ChildTag("sig"),
			TextTag("return type"), ChildTag("ret")
			],
			{
			'sig': B.function_signature_list,
			"ret": B.type,
			'name': B.text
			}))


	#lets keep 'print' a BuiltinFunctionDecl until we have type conversions as first-class functions in lemon,
	#then it can be just a python library call printing strictly strings and we can dump the to_python_str (?)

	def b_print(args):
		o = args['expression'].to_python_str()
		#print o
		log(o)
		return NoValue()

	BuiltinFunctionDecl.create(
		"print",
		b_print,
		[ Text("print"), TypedParameter({'name': Text("expression"), 'type': Ref(B.expression)})])



	build_in(FunctionCallNodecl(), 'call')
	build_in(WorksAs.b("call", "expression"), False)





	def num_arg(name = "number"):
		return TypedParameter({'name':Text(name), 'type':Ref(B.number)})

	def text_arg():
		return TypedParameter({'name':Text("text"), 'type':Ref(B.text)})

	def num_list():
		return  B.list.make_type({'itemtype': Ref(B.number)})

	def num_list_arg():
		return TypedParameter({'name':Text("list of numbers"), 'type':num_list()})



	def pfn(function, signature, return_type = int, **kwargs):
		"""helper function to add a builtin python function"""
		if return_type == int:
			return_type = Ref(B.number)
		elif return_type == bool:
			return_type = Ref(B.bool)
		elif return_type == None:
			return_type = Ref(B.void)

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
	# endregion

	def add_operators():
		#we'll place this somewhere else, but later i guess, splitting this
		#file into some reasonable modules would still create complications
		import operator as op

		pfn(op.floordiv, [num_arg('A'), Text("//"), num_arg('B')])
		pfn(op.truediv,  [num_arg('A'), Text("/"), num_arg('B')])

		pfn(op.abs, [Text("abs("), num_arg(), Text(")")])
		pfn(op.add, [num_arg('A'), Text("+"), num_arg('B')])

		pfn(op.eq,  [num_arg('A'), Text("=="),num_arg('B')], bool)
		pfn(op.ge,  [num_arg('A'), Text(">="),num_arg('B')], bool)
		pfn(op.gt,  [num_arg('A'), Text(">"), num_arg('B')], bool)
		pfn(op.le,  [num_arg('A'), Text("<="),num_arg('B')], bool)
		pfn(op.lt,  [num_arg('A'), Text("<"), num_arg('B')], bool)
		pfn(op.mod, [num_arg('A'), Text("%"), num_arg('B')])
		pfn(op.mul, [num_arg('A'), Text("*"), num_arg('B')])
		pfn(op.neg, [Text("-"), num_arg()])
		pfn(op.sub, [num_arg('A'), Text("-"), num_arg('B')])

		#import math

		def b_squared(arg):
			return arg * arg
		pfn(b_squared, [num_arg(), Text("squared")], name = "squared")

		def b_list_squared(arg):
			return [b_squared(i) for i in arg]
		pfn(b_list_squared, [num_list_arg(), Text(", squared")], num_list(), name = "list squared")

		pfn(sum, [Text("the sum of"), num_list_arg()], name = "summed")

		def b_range(min, max):
			return list(range(min, max + 1))
		pfn(b_range, [Text("numbers from"), num_arg('min'), Text("to"), num_arg('max')],
			num_list(), name = "range", note="inclusive")
	add_operators()




	# region more nodes
	class Serialized(Syntaxed):
		def __init__(self, children):
			#self.status = widgets.Text(self, "(status)")
			#self.status.color = "compiler hint"
			super(Serialized, self).__init__(children)

		def _eval(s):
			return Banana("deserialize me first")

		def on_keypress(self, e):
			if e.key == K_d and e.mod & KMOD_CTRL:
				self.unserialize()
				return True

		def unserialize(self):
			data = self.ch.serialization.pyval
			log("unserializing %s"%data)
			new = deserialize(data, self)
			log("voila:%s"%new)
			self.parent.replace_child(self, new)



	class CustomNodeDef(Syntaxed):
		pass

	build_in(SyntaxedNodecl(Serialized,
				   ["??", ChildTag("last_rendering"), ChildTag("serialization")],
				   {'last_rendering': B.text,
				    'serialization':dict_from_to('text', 'anything')}))

	build_in(SyntaxedNodecl(CustomNodeDef,
				   ["node", ChildTag('name'), "with syntax:", ChildTag("syntax")],
				   {'name' : B.text,
				   'syntax': B.custom_syntax_list}))
	"""this gets us a node defining nodes, so it should have nodecl functionality"""





	class After(Syntaxed):
		pass
	#how to best choose the syntax from within a parent node?
	"""
	build_in(SyntaxedNodecl(After,
	                        ['after', ChildTag('function'), ':\n', ChildTag('body')],
		{'function': B.functionsignatureref,
		 'body': B.statements}))
	"""


"""
class NodeSyntax(Syntaxed):
	pass

build_in(SyntaxedNodecl(NodeSyntax,
			   ["node syntax:", ChildTag("syntax")],
			   {'syntax': b['custom syntax list']}))
"""




"""


class: based on customnode, one level,

how to do views best?



"""



"""
add python_env to Module?










"""
