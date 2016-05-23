# -*- coding: utf-8 -*-

"""

this file defines the AST classes of the language and everything around it.
the philosophy of this codebase is "constant surprise". it keeps you alert.
"kids" and "children" mean the same.
sometimes i use "s" instead of "s".
"ch" is children of syntaxed.
good luck.

"""

autocomplete = True

# region imports
from copy import copy
import json
import collections
from pprint import pformat as pp

from lemon_utils.pizco_signal.util import Signal

from lemon_utils.lemon_six import iteritems, iterkeys, itervalues, unicode
from lemon_utils.notifyinglist import NotifyingList

import element
from element import CHANGED
from menu_items import MenuItem
import widgets
import tags
from tags import *

from lemon_colors import colors
from keys import *
from lemon_utils.utils import flatten, odict, Evil, uniq
from lemon_utils.dotdict import Dotdict
from lemon_args import args


import logging
logger=logging.getLogger("nodes")
info=logger.info
log=logger.debug
warn=logger.warn

from marpa_cffi.marpa_misc import * # valuator actions

tags.asselement = element # for assertions

# endregion
AST_CHANGED = 2

#B is for staging the builtins module and referencing builtin nodes from python code
B = Dotdict()
B._dict = odict()

def build_in(node, name=None, builtins_table = B):
	"""add node to B"""
	if isinstance(node, list):
		#python lets you do this kind of name overriding?
		#how does it know which node is the node you want
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
		assert key not in builtins_table._dict,  repr(key) + " already in builtins:" + repr(node)
		builtins_table[key] = node
	return node

class DelayedCursorMove():
	__slots__ = ['chars', 'node']
	def __init__(s):
		s.chars = 0
		s.node = None

# region utils

def make_union(items: list):
	r = B.union.inst_fresh()
	r.ch["items"].items = items
	r.fix_parents()
	return r


def is_decl(node):
	return isinstance(node, (NodeclBase, ParametricTypeBase, ParametricNodecl))
def is_type(node):
	return is_decl(node) or isinstance(node, (Ref, Exp, Definition, SyntacticCategory, EnumType))

def deref_decl(d):
	if isinstance(d, Ref):
		return deref_decl(d.target)
	elif isinstance(d, Definition):
		return deref_decl(d.type)
	elif is_decl(d) or d == None or isinstance(d, SyntacticCategory):
		return d
	else:
		raise Exception("i dont knwo how to deref "+repr(d)+", it should be a type or something")

def make_list(type_name= 'anything'):
	"instantiate a lemon List of given type"
	return list_of(type_name).inst_fresh()

def list_of(type_name):
	"""create a list type"""
	if type(type_name) == unicode:
		t = B[type_name]
	else:
		t = type_name

	return B.list.instantiate({'itemtype': Ref(t)})

def dict_from_to(key, val):
	"""a helper for creating a type"""
	return B.dict.instantiate({'keytype': Ref(B[key]), 'valtype': Ref(B[val])})

def make_dict(key_type_name, val_type_name):
	return dict_from_to(key_type_name, val_type_name).inst_fresh()

def make_dict_from_anything_to_anything():
	return make_dict('anything', 'anything')

#where does .module.inst_fresh() come from?
#is this a python-ism?
def new_module():
	return B.module.inst_fresh()

def num_arg(name = "number"):
	return TypedParameter({'name':Text(name), 'type':Ref(B.number)})

def str_arg(name="text"):
	return TypedParameter({'name':Text(name), 'type':Ref(B.text)})

def num_list():
	return  list_of(B.number)

def num_list_arg():
	return TypedParameter({'name':Text("list of numbers"), 'type':num_list()})

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
	assert parent
	if 'resolve' in data: # create a Ref pointing to another node
		return resolve(data, parent)
	if not 'decl' in data: # every node must have a type
		raise DeserializationException("no decl key in %s"%data)
	decl = data['decl']
	log("deserializing node with decl %s"%repr(decl))
	if decl == 'Parser': # ok, some nodes are special, we dont have a type for Parser
		return Parser.deserialize(data, parent)
	elif decl == 'defun': # i dont save the exact class of functions definitions, makes it easier to change functions from BuiltinPythonFunctionDecl to FunctionDefinition, for example
		return FunctionDefinitionBase.deserialize(data, parent)
	#if decl == 'varref':
	#	return VarRef.deserialize(data, parent)
	elif isinstance(decl, unicode): # we will look for a nodecl node with this name
		decl = find_decl(decl, parent.nodecls)
		if decl:
			log("deserializing item with decl %s thru class %s"%(decl, decl.instance_class))
			return decl.instance_class.deserialize(data, parent)
		else:
			log("nodecl node not found")
			raise DeserializationException ("cto takoj " + repr(decl))
	elif isinstance(decl, dict): # the node comes with a decl as, basically, its child
		decl = deserialize(decl, parent)
		try:
			return deref_decl(decl).instance_class.deserialize(data, parent)
		except DeserializationException as e:
			log(e)
			return failed_deser(data, parent)
	else:
		raise DeserializationException ("cto takoj " + repr(decl))

def failed_deser(data, parent):
	"""create a Serialized node that holds the data that failed to deserialize"""
	assert parent
	r = Serialized.fresh()
	r.parent = parent
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
			log("found:%s",name)
			return i
	raise DeserializationException ("%s not found in %s"% (repr(name), repr(decls)))


def resolve(data, parent):
	assert parent
	assert(data['resolve'])
	log("resolving %s", data)
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
				dd1,dd2 = deref_decl(decl) ,deref_decl(i.decl)
				log('dd1:%s, dd2:%s'%(dd1,dd2))
				if dd1 == dd2:
					log("in scope:%s",i)
					if i.name == name:
						return i
			raise DeserializationException("node not found: %s ,decl: %s"%(data,decl))

	elif 'class' in data:
		sought_name = data['name']
		sought_class_name = data['class']
		log("looking for name:%s, class:%s", sought_name, sought_class_name)
		for i in scope:
			class_name = i.__class__.__name__.lower()

			if class_name == sought_class_name:
				name = i.name
				log("class:%s, name:%s",class_name, name)
				if name == sought_name:
					return i
		raise DeserializationException("node with name %s and class %s not found"%(sought_name, sought_class_name))

	else:
		raise DeserializationException("dunno how to resolve %s" % data)


#these PersistenceStuff classes are just bunches of functions
#that could as well be in the node classes themselves,
#the separation doesnt have any function besides having them all
#in one place for convenience

class NodePersistenceStuff(object):
	def serialize(s):
		#assert isinstance(s.decl, Ref) or s.decl.parent == s,  s.decl
		r = odict(s.serialize_decl())
		r.updated_with(s._serialize())

	def serialize_decl(s):
		if s.decl:
			#log("serializing decl %s of %s"%(s.decl, s))
			return {'decl': s.decl.serialize()}
		else:
			return {'class': s.__class__.__name__.lower()}

	def unresolvize(s):
		r = odict(
			resolve = True,
			name = s.name)
		r.update(s.serialize_decl())
		return r

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
		assert parent
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
		assert parent
		r = cls()

		r.parent = parent

		placeholder = Text("placeholder")
		placeholder.parent = parent#?maybe rather =r?
		r.decl = deserialize(data['decl'], placeholder)

		assert(r.items == [])
		for i, item_data in enumerate(data['items']):
			pl = Text("placeholder")
			r.add(pl)
			r.items[i] = deserialize(item_data, pl)
			r.items[i].parent = r
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
		assert parent
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
		assert parent
		placeholder = Text("placeholder")
		placeholder.parent = parent
		decl = deserialize(data['target']['decl'], placeholder)
		for i in parent.vardecls_in_scope:
			log('i in parent.vardecls_in_scope:%s',i)
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
			if isinstance(i, widgets.Text):
				r.append(i.value)
			else:
				r.append(i.serialize())
		return r

	@classmethod
	def deserialize(cls, data, parent):
		assert parent
		r = cls(data['slot'])
		r.parent = parent
		log("deserializing Parser "+str(data))
		for i in data['items']:
			if isinstance(i, unicode):
				r.add(widgets.Text(666, i))
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
		assert parent
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
		log('deserializing widgeted value:%s'%data)
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

	def __init__(s):
		"""	__init__ usually takes children or value as arguments.
		fresh() calls it with some defaults (as the user would have it inserted from the menu)
		each class has a decl, which is an object descending from NodeclBase (nodecl for node declaration).
		nodecl can be thought of as a type, and objects pointing to them with their decls as values of that type.
		nodecls have a set of functions for instantiating the values, and those need some cleanup"""
		super().__init__()
		s.runtime = Dotdict() #various runtime data herded into one place
		s.clear_runtime_dict()
		s.fresh = "i think youre looking for inst_fresh, fresh() is a class method, you called it on an instance"
		s.forget_symbols()

	def forget_symbols(s):
		"""clear marpa symbol ids"""
		s._symbol  = None

	@property
	def symbol(s):
		print("gimme node_symbol for", s)
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
		assert v or isinstance(s, Root) or s.isroot,  s
		super().set_parent(v)
		if "value" in s.runtime._dict: #crap
			s.runtime.value.parent = s.parent

	#in python, overriding properties has to be done like this
	parent=property(element.Element.get_parent, set_parent)




	@property
	def parsed(s):
		"all nodes except Parser return themselves"#..hm
		return s

	def scope(s):
		"""lexical scope, what does this node see?"""
		r = []

		if isinstance(s.parent, List):
			r += [x.parsed for x in s.parent.above(s)]

		assert s.parent != None, s.long__repr__()

		r += [s.parent]
		r += s.parent.scope() # note:Root has parent None

		assert(r != None)
		assert(flatten(r) == r)

		return r

	@property
	def nodecls(s):
		return [i for i in s.scope() if isinstance(i, NodeclBase)] #crap:just NodeclBase? what about EnumType?

	@property
	def vardecls_in_scope(s):
		"""what variable declarations does this node see?"""
		r = []

		#if isinstance(s.parent, List):
		#	above = [x.compiled for x in s.parent.above(s)]
		#	r += [i if isinstance(i, VariableDeclaration) for i in above]

		if s.parent != None:
			r += s.parent.vardecls
			r += s.parent.vardecls_in_scope

		assert(is_flat(r))
		return r

	def eval(s):
		"call _eval(), save result to s.runtime"
		r = s._eval()
		assert isinstance(r, Node),  str(s) + "._eval() is borked"

		#if s.isconst: # todo:figure out how const would propagate (to compiler)
		#	s.runtime.value.set(r)
			#log("const" + str(s))
		#else:
		#	s.runtime.value.append(r)
		s.append_value(r)
		return r

	def append_value(s, v):
		"store a result of evaluation or something"
		if not "value" in s.runtime._dict:
			s.runtime.value = make_list('anything')
			s.runtime.value.parent = s.parent #also has to be kept updated in the parent property setter

		s.runtime.value.append(v)
		s.runtime.evaluated = True

	def _eval(s):
		s.runtime.unimplemented = True
		return Text("not implemented")

	def module(s):
		if isinstance(s, Module):
			return s
		else:
			if s.parent != None:
				return s.parent.module()
			else:
				log ("%s has no parent", s)
				return None

	@classmethod
	def fresh(cls, decl=None):
		"make a new instance"
		r = cls()
		if decl:
			r.decl = decl
		return r

	def to_python_str(s):
		return unicode(s)

	@property
	def vardecls(s):
		"""what variables does this node declare"""
		return []

	def tags(elem):
		"""called from Element.render"""
		yield super().tags()
		#add results of eval
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
	def flatten(s):
		"""return yours and all your children/items as a list
		#crap: decls arent included in flatten(?)
		"""
		return flatten(s._flatten())

	def _flatten(s):
		"per-class implementation of flattening"
		if not isinstance(s, (WidgetedValue, EnumVal, Ref, SyntaxedNodecl, FunctionCallNodecl,
			ParametricNodecl, Nodecl, VarRefNodecl, TypeNodecl, VarRef)): #all childless nodes
			warn(str(s)+ " flattens to self")
		return [s]

	def palette(s, scope, text, node):
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

	def delete_child(s, child):
		log("not implemented, go delete someone else's children")

	@staticmethod
	def match(v):
		return False

	def works_as(s, type):
		return False

	def unparen(s):
		return s

class Syntaxed(SyntaxedPersistenceStuff, Node):
	"""
	Syntaxed has some named children, kept in s.ch.
	their types are in s.slots.
	syntax is a list of Tags, and it can contain ChildTag
	"""
	brackets = ("<", ">")
	#brackets = ("", "")
	default_syntax_index = 0
	rank = 0

	def __init__(s, children):
		super().__init__()
		s.check_slots(s.slots)
		s.syntax_index = s.__class__.default_syntax_index
		s.ch = Children()

		assert len(children) == len(s.slots), (children, s.slots)

		#set children from the constructor argument
		for k in iterkeys(s.slots):
			s.set_child(k, children[k])

		# prevent setting new ch keys
		s.ch._lock()
		# prevent setting new attributes
		s.lock()
		#assert isinstance(s.ddecl, SyntaxedNodecl)

	@classmethod
	def register_class_symbol(cls):
		#this is the grand-top-starting symbol for this node type
		r = m.symbol(cls.__name__)
		m.set_symbol_rank(r, cls.rank)
		
		#since we have like class Var(Syntaxed)
		#the Var's decl is the SyntaxedNodecl that actually holds the syntaxes and sits in the declaring module
			
		
		ddecl = deref_decl(cls.decl)
		
		#and a syntaxed can have multiple syntaxes, for now just in a primitive way
		
		for sy in ddecl.instance_syntaxes:
			cls.rule_for_syntax(r, sy, ddecl)
				
		return r



	@classmethod
	def rule_for_syntax(cls, cls_sym, syntax, ddecl):
		syms = []
		
		
		for i in syntax:
		#we build up syms child after child, char after char
		#if autocomplete is on, we create a rule after each addition
		#otherwise we only create a rule for the final, complete, syms

			ti = type(i)

			if ti == unicode:
				for ch in i:
					syms = syms[:]
					syms.append(m.known_char(ch))
					if autocomplete:
						m.rule(cls.__name__, cls_sym, syms, action=lambda x: cls.from_parse(x, syntax))
			elif ti == ChildTag:
				child_type = ddecl.instance_slots[i.name]
				if type(child_type) == Exp:
					x = B.expression.symbol
				else:
					x = deref_decl(child_type).symbol
				if not x:
					log("no type:" + str(i))
					return None
				assert x, child_type
				syms = syms[:]
				syms.append(x)
				if autocomplete:
					m.rule(cls.__name__, cls_sym, syms, action=lambda x: cls.from_parse(x, syntax))
		assert len(syms) != 0
		if not autocomplete:
			m.rule(cls.__name__, cls_sym, syms, action=lambda x: cls.from_parse(x, syntax))

	@classmethod
	def from_parse(cls, p, sy):
		print('from_parse:%s',p)

		r = cls.fresh()
		#info((p, cls, sy))

		s2 = []
		for i in sy:
			if type(i) == unicode:
				for ch in i:
					s2.append(ch)
			else:
				s2.append(i)


		print(sy)
		print(s2)

		si = 0#syntax_item_index

		for i in p:
			if type(i) == unicode:
				assert type(s2[si] == unicode)
			else:
				assert isinstance(i, Element)
				r.ch[s2[si].name] = i

			si+=1


			#if j == len(p): break

		r.fix_parents()
		return r


	@classmethod
	def fresh(cls, decl=None):
		r = cls(cls.create_kids(deref_decl(cls.decl).instance_slots))
		if decl:
			r.decl = decl
		r.fix_parents()
		return r

	def fix_parents(s):
		s._fix_parents(list(s.ch._dict.values()))

	def set_child(s, name, item):
		assert isinstance(name, unicode), repr(name)
		assert isinstance(item, Node)
		item.parent = s
		s.ch[name] = item

	def replace_child(s, child, new):
		"""child name or child value? thats a good question...its child the value!"""
		assert(child in itervalues(s.ch))
		assert(isinstance(new, Node))
		for k,v in iteritems(s.ch):
			if v == child:
				s.ch[k] = new
				new.parent = s
				return
		raise Exception("i dont have that child: "+child)
		#todo:refactor into find_child or something

	def delete_child(s, child):
		for k,v in iteritems(s.ch._dict):
			if v == child:
				s.ch[k] = s.create_kids(s.slots)[k]
				s.ch[k].parent = s
				return

		raise Exception("We should never get here")
		#s.replace_child(child, Parser(b["text"])) #toho: create new_child()

	def _flatten(s):
		assert(isinstance(v, Node) for v in itervalues(s.ch._dict))
		return [s] + [v.flatten() for v in itervalues(s.ch._dict)]

	@staticmethod
	def check_slots(slots):
		if __debug__:
			assert(isinstance(slots, dict))
			for name, slot in iteritems(slots):
				assert(isinstance(name, unicode))
				assert isinstance(slot, (NodeclBase, Exp, ParametricTypeBase, Definition, SyntacticCategory)), "these slots are fucked up:" + str(slots)

	@property
	def syntax(s):
		return s.syntaxes[s.syntax_index]

	def render(s):
		return s.syntax

	def prev_syntax(s):
		s.syntax_index  -= 1
		if s.syntax_index < 0:
			s.syntax_index = 0
		log("previous syntax")
		return CHANGED

	def next_syntax(s):
		s.syntax_index  += 1
		if s.syntax_index == len(s.syntaxes):
			s.syntax_index = len(s.syntaxes)-1
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

	@property
	def name(s):
		"""override if this doesnt work for your subclass"""
		return s.ch.name.pyval

	@property
	def syntaxes(s):
		return s.ddecl.instance_syntaxes

	@property
	def slots(s):
		return s.ddecl.instance_slots

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

	def unparen(s):
		return s.__class__(dict([(k, v.unparen()) for k, v in iteritems(s.ch._dict)]))


class Collapsible(Node):
	"""Collapsible - List or Dict -
	they dont have a title, just a collapse button, right of which the first item is rendered
	"""
	vm_collapsed = 0
	vm_oneline = 1
	vm_multiline = 2

	def __init__(s):
		super().__init__()
		s.view_mode_widget = widgets.NState(s, 0, ("+","v","-"))

	@property
	def view_mode(s):
		return s.view_mode_widget.value
	@view_mode.setter
	def view_mode(s, m):
		s.view_mode_widget.value = m

	def render(s):
		yield [MemberTag('view_mode_widget'), IndentTag()]
		if s.view_mode > 0:
			yield s.render_items()
		yield DedentTag()

	@classmethod
	def fresh(cls, decl):
		#log("decl="+repr(decl))
		r = cls()
		if decl:
			r.decl = decl
		assert(r.decl)
		return r


def replace_thing_in_odict(d:odict, old, new):
	r = odict()
	for k,v in iteritems(d):
		if k == old:
			r[new] = v
		elif v == old:
			r[k] = new
		else:
			r[k] = v
	return r


class Dict(Collapsible):
	def __init__(s):
		super().__init__()
		s.items = odict()

	def replace_child(s, old, new):
		s.items = replace_thing_in_odict(s.items, old, new)
		s.fix_parents()

	def render_items(s):
		r = []
		for key, item in iteritems(s.items):
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

	def fix_parents(s):
		super().fix_parents()
		s._fix_parents(list(s.items.values()))
		s._fix_parents(list(s.items.keys())) # why so complicated?

	def _flatten(s):
		return ([s] + \
		       [k.flatten() for k in iterkeys(s.items)] +
		       [v.flatten() for v in itervalues(s.items) if isinstance(v, Node)])#skip Widgets, for Settings

	@property
	def pyval(s):
		r = {}
		for k,v in iteritems(s.items):
			r[k.pyval] = v.pyval
		return r

	@pyval.setter
	def pyval(s, val):
		new = odict()
		for k, v in iteritems(val):
			new[to_lemon(k)] = to_lemon(v)
		s.items = new
		s.fix_parents()

	"""
	def add(s, kv):
		key, val = kv
		assert(key not in s.items)
		s.items[key] = val
		assert(isinstance(key, unicode))
		assert(isinstance(val, element.Element))
		val.parent = s
		return val
	"""

class List(ListPersistenceStuff, Collapsible):
	easily_instantiable = True
	#todo: view sorting:how and why? separate view objects?
	def __init__(s):
		super().__init__()
		s.items = []
		s.decl = Ref(B.list_of_anything)

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
		if x[1] == 'nulled': x[1] = []
		assert type(x[1]) == list
		r = List()
		r.items = x[1][::2]
		r.view_mode = r.vm_multiline
		r.fix_parents()
		return r

	def render_items(s):
		opening, between, closing = ('[', ', ', ']') if s.view_mode == 1 else ('[ \n', '\n', '\n]')
		yield opening
		for i, item in enumerate(s.items):
			yield [AttTag(Att.item_index, (s, i)), zwe_tag]
			if i != 0: yield between
			yield [ElementTag(item),EndTag()]
		yield [AttTag('list_end',555), zwe_tag, closing, EndTag()]

	def __getitem__(s, i):
		return s.items[i]

	def __setitem__(s, i, v):
		s.items[i] = v
		v.parent = s

	def fix_parents(s):
		super(List, s).fix_parents()
		s._fix_parents(s.items)

	@property
	def slots(s):
		return [s.item_type]

	def item_index(s, atts):
		li = atts.get(Att.item_index)
		if li and li[0] == s:
			return li[1]

	def _eval(s):
		r = List()
		r.decl = s.decl.copy()
		r.items = [i.eval() for i in s.items]
		r.fix_parents()
		return r

	def copy(s):
		r = List()
		r.decl = s.decl.copy()
		r.items = [i.copy() for i in s.items]
		r.fix_parents()
		return r

	@property
	def pyval(s):
		return [i.pyval for i in s.items]
	@pyval.setter
	def pyval(s, val):
		s.items = [to_lemon(i) for i in val]
		s.fix_parents()

	def _flatten(s):
		return [s] + flatten([v.flatten() for v in s.items])

	def replace_child(s, child, new):
		assert(child in s.items)
		s.items[s.items.index(child)] = new
		new.parent = s

	def add(s, item):
		
		item.parent = s
		s.items.append(item)
		return item

	def newline(s, pos=-1):
		p = Parser(0)
		p.parent = s
		if pos == -1:
			s.items.append(p)
		else:
			s.items.insert(pos, p)
		return p

	def newline_with(s, node):
		s.newline.add(node)

	@property
	def item_type(s):
		assert hasattr(s, "decl"),  "parent="+str(s.parent)+" contents="+str(s.items)
		ddecl = s.ddecl
		assert isinstance(ddecl, ParametricListType), s
		r = s.ddecl.ch.itemtype
		#log('item_type',r)
		return r

	def above(s, item):
		assert item in s.items,  (item, item.parent, s)
		r = []
		for i in s.items:
			if i == item:
				return r
			else:
				r.append(i)

	def below(s, item):
		assert item in s.items,  (item, item.parent)
		return s.items[s.items.index(item):]

	def to_python_str(s):
		return "[" + ", ".join([i.to_python_str() for i in s.items]) + "]"

	def delete_child(s, ch):
		if ch in s.items:
			s.items.remove(ch)

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.item_type)+"')"

	@property
	def val(s):
		"""
		for "historic" reasons. when acting as a list of eval results.
		during execution, results of evaluation of every node is appended,
		so there is a history available.
		current value is the last one.
		we might split this out into something like EvalResultsList
		"""
		return s[-1]

	def append(s, x):
		"""like add, but returns the item. historic reasons."""
		assert(isinstance(x, Node))
		s.items.append(x)
		x.parent = s
		return x
	"""
	def set(s, x):
		#constants should call this..but if they are in a Parser, isconst wont propagate yet
		assert(isinstance(x, Node))
		if len(s) > 0:
			s[0] = x
		else:
			super(val, s).append(x)
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
		s.decl = Ref(B.statements)

	@classmethod
	def fresh(cls, decl=None):
		r = cls()
		r.newline()
		return r

	@property
	def item_type(s):
		return B.statement

	def run(s):
		[i.eval() for i in s.items]
		return Text("it ran.")

	def _eval(s):
		results = [i.eval() for i in s.items]
		if len(results) == 0:
			return NoValue()
		else:
			return results[-1]

	#@property
	#def parsed(s):#i wonder if this is wise #nope, it wasnt
	#	r = Statements()
	#	r.parent = s###
	#	r.items = [i.parsed for i in s.items]
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
	def __init__(s):
		super(NoValue, s).__init__()
	def render(s):
		return [TextTag('void')]
	def to_python_str(s):
		return "no value"
	def eq_by_value(a, b):
		return True

class Banana(Node):
	help=["runtime error. try not to throw these."]
	def __init__(s, text="error text"):
		super(Banana, s).__init__()
		s.text = text
	def render(s):
		return ["error:", TextTag(s.text)]
	def to_python_str(s):
		return "runtime error"

class Bananas(Node):
	"""https://www.youtube.com/watch?v=EAmChFTLP4w&feature=youtu.be&t=2m19s"""
	help=["parsing error. your code is bananas."]
	def __init__(s, contents=[]):
		super(Bananas, s).__init__()
		s.contents = contents
	def render(s):
		if len(s.contents) > 0:
			return [TextTag(s.to_python_str())]
		else:
			return [TextTag("?")]
	def to_python_str(s):
		return "couldnt parse " + str(len(s.contents)) + " items:"+str(s.contents)
	def _eval(s):
		return Bananas(s.contents)

class WidgetedValue(WidgetedValuePersistenceStuff, Node):
	"""basic one-widget value"""
	is_const = True#this doesnt propagate to Parser yet, but anyway, this node always evaluates to the same value
	#during a program run. guess its waiting for type inference or something
	def __init__(s):
		super(WidgetedValue, s).__init__()	

	@property
	def pyval(s):
		return s.widget.value

	@pyval.setter
	def pyval(s, val):
		s.widget.value = val

	@property
	def text(s):
		return s.widget.text

	@text.setter
	def text(s, v):
		s.widget.text = v

	def render(s):
		return [MemberTag('widget')]

	def to_python_str(s):
		return str(s.pyval)

	def copy(s):
		return s.__class__(s.pyval)

	def eq_by_value(a,b):
		return a.pyval == b.pyval

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.pyval)+"')"

class Number(WidgetedValue):
	easily_instantiable = True
	def __init__(s, value="0"):
		super(Number, s).__init__()
		s.widget = widgets.Number(s, value)
		s.widget.brackets = ('','')

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

	def _eval(s):
		return Number(s.pyval)

	@staticmethod
	def match(text):
		if text.isdigit():
			return True
			

class Text(WidgetedValue):
	easily_instantiable = True
	brackets = ('[', ']')
	def __init__(s, value="", debug_note=""):
		super(Text, s).__init__()
		s.widget = widgets.Text(s, value)
		s.brackets_color = colors.text_brackets
		s.debug_note = debug_note


	@classmethod
	def register_class_symbol(cls):
		clsstr = str(cls)
		log("registering "+clsstr+" grammar")
		double_slash = m.known_string('//')
		slashed_end =  m.known_string('/'+cls.brackets[1])
		body_part = m.symbol(clsstr+'_body_part')
		m.rule(clsstr+'_body_part_is_double_slash', body_part, double_slash)
		m.rule(clsstr+'_body_part_is_slashed_end', body_part, slashed_end)
		m.rule(clsstr+'_body_part_is_nonspecial_char', body_part, m.syms.nonspecial_char)
		m.rule(clsstr+'_body_part_is_known_char', body_part, m.syms.known_char)
		body = m.symbol('body')
		m.sequence(clsstr+'_body is seq of body part', body, body_part, join)
		text = m.symbol(clsstr)
		opening =  m.known_string(cls.brackets[0])
		closing =  m.known_string(cls.brackets[1])
		m.rule(clsstr+'_is_[body]', text, [opening, body, closing], cls.from_parse)
		return text

	@classmethod
	def from_parse(cls, args):
		return cls(args[1])

	def _eval(s):
		return Text(s.pyval)



class Comment(Text):
	brackets = ('/*', '*/')


class Identifier(WidgetedValue):
	def __init__(s, value=""):
		super().__init__()
		s.widget = widgets.Text(s, value)

	@classmethod
	def register_class_symbol(cls):
		#the symbol here is meant a marpa symbol, 
		#grammars are made up of symbols and rules
		#so, here we have a little builtin grammar for Identifier
		#it prolly allows more than we want now but w/e
		#its actually the menu class that goes and collects this
		#and then calls the marpa thread
		
		log("registering identifier grammar")
		body_part = m.symbol('body_part')
		m.rule('identifier_body_part_is_nonspecial_char', body_part, m.syms.nonspecial_char)
		m.rule('identifier_body_part_is_known_char', body_part, m.syms.known_char)
		r = m.symbol('Identifier')
		m.sequence('identifier is seq of body part', r, body_part, cls.from_parse)
		return r

	@classmethod
	def from_parse(cls, args):
		return cls(''.join(args))


class RestrictedIdentifier(WidgetedValue):
	def __init__(s, value=""):
		super().__init__()
		s.widget = widgets.Text(s, value)

	@classmethod
	def register_class_symbol(cls):
		log("registering restricted identifier grammar")
		body_part = m.symbol('body_part')

		allowed = []
		for rng in ['az', 'AZ']:
			allowed.extend([chr(x) for x in range(ord(rng[0]),ord(rng[1]))])
		allowed.extend([ch for ch in '_-'])
		for ch in allowed:
			m.rule('restricted_identifier_body_part_is_', body_part, m.known_char(ch))
		
		r = m.symbol('Identifier')
		m.sequence('identifier is seq of body part', r, body_part, cls.from_parse)
		return r

	@classmethod
	def from_parse(cls, args):
		return cls(''.join(args))




class Root(Dict):
	def __init__(s):
		super(Root, s).__init__()
		s.parent = None
		s.decl = None
		s.delayed_cursor_move = DelayedCursorMove()
		#the frontend moves the cursor by this many chars after a render()
		## The reason is for example a textbox recieves a keyboard event,
		## appends a character to its contents, and wants to move the cursor,
		## but before re-rendering, it might move it beyond the end of file
		s.indent_length = 4 #not really used but would be nice to have it variable
		s.changed = True

	def render(s):
		#there has to be some default color for everything, the rendering routine looks for it..
		return [ColorTag(colors.fg)] + s.render_items() + [EndTag()]

	def delete_child(s, child):
		log("I'm sorry Dave, I'm afraid I can't do that.")

	def delete_self(s):
		log("I'm sorry Dave, I'm afraid I can't do that ")

	#def okay(s):
	#	recursively check parents?

	def scope(s):
		# deserialization needs this
		s.root["builtins"].ch.statements.parsed




class Module(Syntaxed):
	"""module or program"""
	special_scope = None
	def __init__(s, kids):
		super(Module, s).__init__(kids)
		#s.sortedview = SortableStatements(s)
		s.ch.statements.view_mode = Collapsible.vm_collapsed

	def add(s, item):
		s.ch.statements.add(item)

	def __getitem__(s, i):
		return s.ch.statements[i]

	def __setitem__(s, i, v):
		s.ch.statements[i] = v

	def clear(s):
		st = s.ch.statements
		#print "flatten:", st.flatten()
		for i in st.flatten():
			i.clear_runtime_dict()

	def run(s):
		s.clear()
		return s.ch.statements.run()

	def run_line(s, node):
		s.clear()
		while node != None and node not in s.ch.statements.items:
			node = node.parent
		if node:
			return node.eval()

	@property
	def file_name(s):
		r = s.ch.file.pyval
		if r == "":
			r = 'test_save.lemon.json'
		return r

	def reload(s):
		log(load_module(s.file_name, s))

	def save(s):
		#import yaml
		#s = yaml.dump(s.serialize(), indent = 4)
		#open('test_save.lemon', "w").write(s)
		#log(s)
		#todo easy: find a json module that would preserve odict ordering (or hjson)
		import json
		out = json.dumps(s.serialize(), indent = 4)
		with open(s.file_name, "w") as f:
			f.write(out)
			f.close()
		#log(out)
		log("saved to "+s.file_name)
		#except Exception as e:
		#	log(e)
		#	raise e

	def scope(s):

		if s == s.root["builtins"]:
			return [] # builtins dont see anything
		else:
			if s.special_scope:
				print ('....')
				r = []
				for i in s.special_scope:
					if isinstance(i, Module):
					#we dont honor the module's scope()
						for x in i.ch.statements.parsed.items:
							r.append(x)
					else:
						r.append(i)
				return r
			else:

				r = s.root["builtins"].ch.statements.parsed.items[:]

				for module in s.root['library'].items:
					if not isinstance(module, Module):
						continue
					if module != s:
						r += [x.parsed for x in module.ch.statements.parsed.items]
					#log(module)
					#log(r)
				return r




# endregion

# region nodecls and stuff

class Ref(RefPersistenceStuff, Node):
	"""points to another node.
	if a node already has a parent, you just want to point to it, not own it"""
	#todo: separate typeref and ref?..varref..?
	def __init__(s, target):
		super(Ref, s).__init__()
		s.target = target

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

	def render(s):
		return [TextTag('*'), ArrowTag(s.target), TextTag(s.name)]

	@property
	def name(s):
		return s.target.name

	def works_as(s, type):
		return s.target.works_as(type)
	def inst_fresh(s):
		"""you work as a type, you have to provide this"""
		return s.target.inst_fresh()
	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.target)+"')"
	def eq_by_value(a, b):
			if a.target == b.target:
				log("saying %s equals %s"%(a,b))
				return True
	def copy(s):
		return Ref(s.target)


class VarRef(VarRefPersistenceStuff, Node):
	def __init__(s, target):
		super(VarRef, s).__init__()
		s.target = target
		assert isinstance(target, (UntypedVar, TypedParameter))
		#log("varref target:"+str(target))

	def render(s):
		return [TextTag('$'), ArrowTag(s.target), TextTag(s.name)]

	@property
	def name(s):
		return s.target.name

	def _eval(s):
		#it is already has a value
		return s.target.runtime.value.val

class Exp(Node):
	"""used to specify that an expression (something that evaluates to, at runtime) of
	some type, as opposed to a node of that type, is expected"""
	def __init__(s, type):
		super(Exp, s).__init__()
		s.type = type

	def render(s):
		return [MemberTag("type"), TextTag('expr')]

	@property
	def name(s):
		return s.type.name + " expr"

class NodeclBase(Node):
	"""a base for all nodecls. Nodecls declare that some kind of nodes can be created,
	know their python class ("instance_class"), syntax and shit. Think types.
	usually does something like instance_class.decl = s, so we can instantiate the
	classes in code without going thru a corresponding nodecl.inst_fresh()"""
	help = None
	def __init__(s, instance_class):
		super(NodeclBase, s).__init__()
		s.instance_class = instance_class
		instance_class.decl = Ref(s)
		s.decl = None
		s.example = None

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
		# t(str(s.instance_class))]

	@property
	def name(s):
		return s.instance_class.__name__.lower()

	def instantiate(s, kids):
		return s.instance_class(kids)

	def inst_fresh(s, decl=None):
		""" fresh creates default children"""
		return s.instance_class.fresh(decl)

	def palette(s, scope, text, node):
			return [PaletteMenuItem(s.instance_class.fresh())]

	def works_as(s, type):
		if isinstance(type, Ref):
			type = type.target
		if s == type: return True
		#todo:go thru Definitions and SyntacticCategories...this is a prolog thing

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.instance_class)+"')"


class TypeNodecl(NodeclBase):
	""" "pass me a type" kind of value
	instantiates Refs ..maybe should be TypeRefs
	"""
	help = ["points to another node, like using an identifier. Used only for pointing to types."]
	def __init__(s):
		super().__init__(Ref)

	def palette(s, scope, text, node):
		nodecls = [x for x in scope if isinstance(x, (NodeclBase))]
		return [PaletteMenuItem(Ref(x)) for x in nodecls]

	def make_example(s):
		return Ref(B.module)
#so this was my approach...nodes are types..
#misses a parser aparently








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

	def __init__(s):
		super().__init__(VarRef)


	def palette(s, scope, text, node):
		r = []
		for x in node.vardecls_in_scope:
			assert isinstance(x, (UntypedVar, TypedParameter))
			r += [PaletteMenuItem(VarRef(x))]
		return r
"""
	def palette(s, scope, text):
		r = []
		for x in scope:
			xc=x.compiled
			for y in x.vardecls:
				yc=y.compiled
				#log("vardecl compiles to: "+str(yc))
				if isinstance(yc, (UntypedVar, TypedParameter)):
					#log("vardecl:"+str(yc))
					r += [PaletteMenuItem(VarRef(yc))]
		#log (str(scope)+"varrefs:"+str(r))
		return r
"""
class ExpNodecl(NodeclBase):
	def __init__(s):
		super(ExpNodecl, s).__init__(Exp)

	def palette(s, scope, text, node):
		nodecls = [x for x in scope if isinstance(x, (NodeclBase))]
		return [PaletteMenuItem(Exp(x)) for x in nodecls]

class Nodecl(NodeclBase):
	"""for simple nodes (Number, Text, Bool)"""
	def __init__(s, instance_class):
		super(Nodecl, s).__init__(instance_class)
		instance_class.decl = Ref(s)
		#print("building in",s.name)
		#build_in(s, s.name)
		#instance_class.name = s.name

	def make_example(s):
		return s.inst_fresh()

	def palette(s, scope, text, node):
		i = s.instance_class
		m = i.match(text)
		if m:
			value = i(text)
			score = 300
		else:
			value = i()
			score = 0
		return PaletteMenuItem(value, score)

class SyntaxedNodecl(NodeclBase):
	"""
	A Nodecl for a class derived from Syntaxed.
	instance_slots holds types of children, not Ref'ed.
	 children themselves are either Refs (pointing to other nodes),
	 or owned nodes (their .parent points to us)
	"""
	def __init__(s, instance_class, instance_syntaxes, instance_slots):
		super(SyntaxedNodecl , s).__init__(instance_class)
		s.instance_slots = dict([(k, B[i] if isinstance(i, unicode) else i) for k,i in iteritems(instance_slots)])
		if isinstance(instance_syntaxes[0], list):
			s.instance_syntaxes = instance_syntaxes
		else:
			s.instance_syntaxes = [instance_syntaxes]
		s.example = None

	def make_example(s):
		return s.inst_fresh()



class ParametricTypeBase(Syntaxed):
	def inst_fresh(s, decl=None):
		r = s.instance_class()
		if decl == None:
			decl = s
		r.decl = Ref(decl)
		return r

	@property
	def name(s):
		return s.instance_class.__name__ + " type"

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.ch)+"')"

class ParametricDictType(ParametricTypeBase):
	instance_class = Dict

class ParametricListType(ParametricTypeBase):
	instance_class = List


	#@property
	#def refsyntax(s):
	#damn this is just all wrong. name should return something like "list of numbers"
	#should i expose a wrapper for project that would return a string?
	#or do we want to display the name as a node?
	#you cant render a different nodes syntax as your own
	#make a new kind of tag for this?


class ParametricNodecl(SyntaxedNodecl):
	"""says that "list of <type>" declaration could exist, instantiates it (ParametricType)
	only non Syntaxed types are parametric now(list and dict),
	so this contains the type instance's syntax and slots (a bit confusing)"""
	"""
	def __init__(s, value_class, type_syntax, type_slots):
		super(ParametricNodecl, s).__init__(ParametricType)
		s.instance_slots = type_slots
		s.instance_syntaxes = [type_syntax]
		s.value_class = value_class

	def make_type(s, kids):
		return ParametricType(kids, s)

	def palette(s, scope, text, node):
		return [PaletteMenuItem(ParametricType.fresh(s))]
	#def obvious_fresh(s):
	#if there is only one possible node type to instantiate..
	"""


class EnumVal(Node):
	def __init__(s, decl, value):
		super(EnumVal, s).__init__()
		s.decl = decl
		s.value = value

	@property
	def pyval(s):
		return s.value

	@pyval.setter
	def pyval(s, val):
		s.value = val

	def render(s):
		return [TextTag(s.to_python_str())]

	def to_python_str(s):
		text = s.decl.ch.options[s.value].parsed
		assert isinstance(text, Text), text
		return text.pyval

	def copy(s):
		return s.eval()

	def _eval(s):
		return EnumVal(s.decl, s.value)

class EnumType(ParametricTypeBase):
	"""works as a type but doesnt descend from Nodecl. Im just trying stuff..."""
	def __init__(s, children):
		s.instance_class = EnumVal
		super(EnumType, s).__init__(children)
	def palette(s, scope, text, node):
		r = [PaletteMenuItem(EnumVal(s, i)) for i in range(len(s.ch.options.items))]
		#print ">",r
		return r
	def works_as(s, type):
		if isinstance(type, Ref):
			type = type.target
		if s == type: return True
	def inst_fresh(s):
		return EnumVal(s, 0)
#i *could* add register_class_s









class SyntacticCategory(Syntaxed):
	help=['this is a syntactical category(?) of nodes, used for "statement" and "expression"']

	def __init__(s, children):
		super(SyntacticCategory, s).__init__(children)

	def register_symbol(s):
		s._symbol = lhs = m.symbol(s.name)

class WorksAs(Syntaxed):
	help=["declares a subtype relation between two existing types"]
	def __init__(s, children):
		super(WorksAs, s).__init__(children)

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
		
		if isinstance(sub, unicode):
			sub = B[sub]
		if isinstance(sup, unicode):
			sup = B[sup]
			
		return cls({'sub': Ref(sub), 'sup': Ref(sup)})

class Definition(Syntaxed):
	"""should have type functionality (work as a type)"""
	help=['used just for types, currently.']
	def __init__(s, children):
		super(Definition, s).__init__(children)

	def inst_fresh(s):
		return s.ch.type.inst_fresh(s)

	def palette(s, scope, text, node):
		return s.ch.type.palette(scope, text, None)

	@property
	def type(s):
		return s.ch.type.parsed

class Union(Syntaxed):
	help=['an union of types means that any type will satisfy']
	def __init__(s, children):
		super(Union, s).__init__(children)

# endregion
"""
class ListOfAnything(ParametricType):

	def palette(s, scope, text, node):
		#log(s.ch._dict)
		i = s.inst_fresh()
		i.view_mode = 1
		i.newline()
		return [PaletteMenuItem(i)]
	def works_as(s, type):
		return True
"""
class UntypedVar(Syntaxed):
	easily_instantiable = True
	def __init__(s, children):
		super(UntypedVar, s).__init__(children)


class For(Syntaxed):
	def __init__(s, children):
		super(For, s).__init__(children)

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
	def __init__(s, children):
		s.it = B.untypedvar.inst_fresh()
		s.it.ch.name.pyval = "it"
		super(VarlessFor, s).__init__(children)

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
	def __init__(s, children):
		super(If, s).__init__(children)

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
	def __init__(s, children):
		super(Else, s).__init__(children)

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
	def __init__(s, kids):
		super(Filter, s).__init__(kids)
"""
# endregion

# region parser

def even_out(items):
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
		index = find_same_type_pair(items, widgets.Text)
		if index == None: break
		items[index] = widgets.Text(items[index].value + items[index+1].value)
		del items[index+1]

	#find adjacent Nodes and put an empty Text between
	while True:
		index = find_same_type_pair(items, Node)
		if index == None: break
		items.insert(index+1, widgets.Text())

	#ensure Text at beginning and end
	if type(items[0]) != widgets.Text: items.insert(0, widgets.Text())
	if type(items[-1]) != widgets.Text: items.append(widgets.Text())


class ParserBase(Node):

	"""
	{Parser node}
	"""

	def __init__(s):
		super(ParserBase, s).__init__()
		s.items = NotifyingList()
		#s.items.append(widgets.Text(s,"x"))
		s.decl = None
		s.on_edit = Signal()
		s.brackets_color = colors.compiler_brackets
		s.brackets = ('{', '}')
		s.reregister = False

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

	def __getitem__(s, i):
		return s.items[i]

	@property
	def nodes(s):
		return [i for i in s.items if isinstance(i, Node) ]

	def fix_parents(s):
		super(ParserBase, s).fix_parents()
		s._fix_parents(s.nodes)

	def _flatten(s):
		return [s] + flatten([v.flatten() for v in s.items if isinstance(v, Node)])

	def add(s, item):
		s.items.append(item)
		assert isinstance(item, (widgets.Text, Node) ), repr(item)
		#if isinstance(item, Node):
		item.parent = s

	def render(s):
		if len(s.items) == 0: # no items, show the gray type hint
			return s.empty_render()

		for i, item in enumerate(s.items):
			yield [
				AttTag(Att.item_index, (s, i)),
				ElementTag(item),
				EndTag()]

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
			s.root.delayed_cursor_move.node = fch
		#todo
		#elif isinstance(node, FunctionCall):
		#	if len(node.args) > 0:
		#		s.root.post_render_move_caret = node.args[0]
		#elif isinstance(node, WidgetedValue):
		#	if len(node.widget.text) > 0:
		#		s.root.delayed_cursor_move.chars += 2
				#another hacky option: post_render_move_caret_after
				#nonhacky option: render out a tag acting as an anchor to move the cursor to
				#this would be also useful above
		elif isinstance(node, List):
			if len(node.items) > 0:
				s.root.delayed_cursor_move.node = node.items[0]
		#todo etc. make the cursor move naturally

	def delete_child(s, child):
		log("del")
		del s.items[s.items.index(child)]

	def replace_child(s, child, new):
		s.items[s.items.index(child)] = new
		s.fix_parents()

class Parser(ParserPersistenceStuff, ParserBase):
	def __init__(s, slot):
		super(Parser, s).__init__()
		s.slot = slot

	@property
	def type(s):
		return s.parent.slots[s.slot]

	def copy(s):
		r = Parser(s.slot)
		for i in s.items:
			if isinstance(i, unicode666):
				x = i
			else:
				x = i.copy()
			r.add(x)
		return r

	def empty_render(s):
		return [ColorTag(colors.parser_hint), TextTag('('+s.type.name+')'), EndTag()]

	@property
	def parsed(s):
		#default result:		#raise an exception?
		r = Bananas(s.items)

		if len(s.items) == 1:
			i0 = s.items[0]
			if isinstance(i0, Node):
				r = i0
			else: #widgets.Text
				#demodemodemo
				type = s.type
				if isinstance(s.type, Exp):
					type = s.type.type
				if isinstance(type, Ref):
					type = type.target

				i0 = i0.text
#				if type == b['number']:
				if Number.match(i0):
					r = Number(i0)

				if type == B.text:
					r = Text(i0)

		r.parent = s
		return r

	def _eval(s):
		return s.parsed.eval()

	"""
	def replace_child(s, child, new):
		assert(child in s.items)
		s.items[s.items.index(child)] = new
		new.parent = s
		#add a blank at the end
		p = SomethingNew()
		p.parent = s
		s.items.append(p)
	"""
	"""
	def eval(s):
		i = s.items[0]
		i.eval()
		s.runtime = i.runtime
		return s.runtime.value.val
	"""

	def menu_item_selected(s, item, atts=None):
		return s.menu_item_selected_for_child(item)

	#todo: make previous item the first child of the inserted item if applicable
	def menu_item_selected_for_child(s, item):
		#if isinstance(item, (LeshMenuItem)):
		#	return False#hack
		if isinstance(item, ParserMenuItem):
			node = item.value
			#if child_index != None:
			#	s.items[child_index] = node
			#else:#?
			s.items.clear()
			s.items.append(node)
			node.parent = s
			s.post_insert_move_cursor(node)
			return True
		elif isinstance(item, DefaultParserMenuItem):
			return False
		else:
			raise Exception("whats that shit, cowboy? %s?"%item)

	def long__repr__(s):
		return object.__repr__(s) + "(for type '"+str(s.type)+"')"

class ParserMenuItem(MenuItem):
	def __init__(s, value:Node, score = 0):
		super(ParserMenuItem, s).__init__()
		s.value = value
		value.parent = s
		s.scores = Dotdict()
		if score != 0:  s.scores._ = score
		s.brackets_color = colors.parser_menu_item_brackets

	@property
	def score(s):
		#print s.scores._dict
		return sum([i if not isinstance(i, tuple) else i[0] for i in itervalues(s.scores._dict)])

	def tags(s):
		return [MemberTag('value'), ColorTag(colors.menu_item_extra_info), " - "+str(s.value.__class__.__name__)+' ('+str(s.score)+')', EndTag()]

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.value)+"')"

class PaletteMenuItem(ParserMenuItem):
	def __init__(s, value, score=0):
		super().__init__(value, score)
		s.brackets_color = (0,0,0)

class DefaultParserMenuItem(MenuItem):
	def __init__(s, text):
		super().__init__()
		s.text = text
		s.brackets_color = colors.default_parser_menu_item_brackets

	def tags(s):
		return [TextTag(s.text)]
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
	def __init__(s, children):
		super(TypedParameter, s).__init__(children)
	@property
	def type(s):
		return s.ch.type.parsed


class UnevaluatedParameter(FunctionParameterBase):
	"""this argument will be passed to the called function as is, without evaluation"""
	def __init__(s, children):
		super(UnevaluatedParameter, s).__init__(children)
	@property
	def type(s):
		return s.ch.argument.type

class FunctionDefinitionBase(Syntaxed):

	def __init__(s, children):
		super(FunctionDefinitionBase, s).__init__(children)

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
		'valuator action, takes an array of argument nodes, presumably'
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
	def params(s):
		r = odict([(i.name, i) for i in s.sig if isinstance(i, FunctionParameterBase)])
		#for i in itervalues(r):
		#	assert(i.parent)
		return r

	@property
	def sig(s):
		sig = s.ch.sig.parsed

		#check..
		for i in sig.items:
			assert(i.parent)

		#check..
		if not isinstance(sig, List):
			log("sig did not parse to list but to %s", repr(sig))
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
		#print ">", r
		return r

	def typecheck(s, args):
		for name, arg in iteritems(args):
			#if not arg.type.eq(s.arg_types[i])...
			if not hasattr(arg, 'decl'):
				return Banana(str(arg) +" ?! ")
			expected_type = s.params[name].type
			if isinstance(expected_type, Ref) and hasattr(arg, 'decl') and isinstance(arg.decl, Ref):
				if not arg.decl.target == expected_type.target:
					log("well this is maybe bad, decl %s of %s != %s" % (arg.decl, arg, expected_type))
					return Banana(str(arg.decl.name) +" != "+str(expected_type.name))
		return True


	def call(s, args):
		"""common for all function definitions"""
		evaluated_args = {}
		for name, arg in iteritems(args):
			if not isinstance(arg, UnevaluatedParameter):
				evaluated_args[name] = arg.eval()
			else:
				evaluated_args[name] = arg.parsed
		log("evaluated_args:%s", [i.long__repr__() for i in itervalues(evaluated_args)])

		assert(len(evaluated_args) == len(s.params))
		r = s._call(evaluated_args )
		assert isinstance(r, Node), "_call returned "+str(r)
		return r

	def _eval(s):
		"""this is when the declaration is evaluated, not when we are called"""
		return Text("ok, function was declared.")
	"""
	def _unresolvize(s):
		#return dict(super(FunctionDefinitionBase, s).un,
		return {
		        'function':True,
		        'sig':[i.serialize() for i in s.sig],
       			'ret': s.ret,
		}
	"""

	def palette(s, scope, text, node):
		return [PaletteMenuItem(FunctionCall(s))]


"""for function overloading, we could have a node that would be a "Variant" of
	an original function, with different arguments.
"""


class FunctionDefinition(FunctionDefinitionPersistenceStuff, FunctionDefinitionBase):
	"""function definition in the lemon language"""
	def __init__(s, children):
		super(FunctionDefinition, s).__init__(children)

	def _call(s, call_args):
		s.copy_args(call_args)
		#log(call_args)
		return s.ch.body.eval()

	def copy_args(s, call_args):
		for k,v in iteritems(call_args):
			assert isinstance(k, unicode)
			assert isinstance(v, Node)
			s.params[k].append_value(v.copy())


"""
class PassedFunctionCall(Syntaxed):
	def __init__(s, definition):
		super(FunctionCall, s).__init__()
		assert isinstance(definition, FunctionDefinition)
		s.definition = definition
		s.arguments = List([Placeholder() for x in range(len(s.definition.signature.items.items))], vertical=False) #todo:filter out Texts

	def render(s):
		r = ['(call)']
		for i in s.definition.signature.items:
			if isinstance(i, Text):
				r += [(i.widget.text)]
			elif isinstance(i, ArgumentDefinition):
				r += [ElementTag(s.arguments.items[i])]

		return r
"""


class BuiltinFunctionDecl(FunctionDefinitionBase):
	"""dumb and most powerful builtin function kind,
	leaves type-checking to the function"""
	def __init__(s, children):
		s._name = 777
		s.fun = 777
		super(BuiltinFunctionDecl, s).__init__(children)

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

	def _call(s, args):
		return s.fun(args)
		# todo use named *args i guess

	@property
	def name(s):
		return s._name

	#def palette(s, scope, text, node):
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
	def __init__(s, children):
		s.ret= 777
		s.note = 777
		s.pass_root = False # pass root as first argument to the called python function? For internal lemon functions, obviously
		super(BuiltinPythonFunctionDecl, s).__init__(children)

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

	def _call(s, args):
		#translate args to python values, call python function
		checker_result = s.typecheck(args)
		if checker_result != True:
			return checker_result
		pyargs = []
		if s.pass_root:
			pyargs.append(s.root)
		for i in s.sig:
			if not isinstance(i, Text): #typed or untyped argument..
				pyargs.append(args[i.name].pyval)
		python_result = s.fun(*pyargs)
		lemon_result = s.ret.inst_fresh()
		lemon_result.pyval = python_result #todo implement pyval assignments
		return lemon_result

	#def palette(s, scope, text, node):
	#	return []


















class FunctionCall(FunctionCallPersistenceStuff, Node):
	def __init__(s, target):
		super(FunctionCall, s).__init__()
		assert isinstance(target, FunctionDefinitionBase)
		s.target = target
		for i in itervalues(s.target.params):
			assert not isinstance(i.type, Parser), "%s to target %s is a dumbo" % (s, s.target)
		s.args = dict([(name, Parser(name)) for name, v in iteritems(s.target.params)]) #this should go to fresh(?)
		s.fix_parents()

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

	def replace_child(s, child, new):
		assert(child in s.args)
		s.args[s.args.index(child)] = new
		new.parent = s

	def render(s):
		sig = s.target.sig
		assert isinstance(sig, list)
		assert len(s.args) == len(s.target.params),\
			(len(s.args),len(s.target.params),s.args, s.target.params,s, s.target)
		r = []
		for v in sig:
			if isinstance(v, Text):
				r += [TextTag(v.pyval)]
			elif isinstance(v, TypedParameter):
				r += [ElementTag(s.args[v.name])]
			else:
				raise Exception("item in function signature is"+str(v))
		return r

	@property
	def name(s):
		return s.target.name

	def _flatten(s):
		return [s] + flatten([v.flatten() for v in itervalues(s.args)])


class FunctionCallNodecl(NodeclBase):
	"""a type of FunctionCall nodes,
	offers function calls thru palette()"""
	def __init__(s):
		super(FunctionCallNodecl, s).__init__(FunctionCall)
	def palette(s, scope, text, node):
		#override NodeclBase palette() which returns a menuitem with a fresh() instance_class,
		#FunctionCall cant be instantiated without a target.
		return []
		#the stuff below is now performed in FunctionDefinitionBase
#		decls = [x for x in scope if isinstance(x, (FunctionDefinitionBase))]
#		return [PaletteMenuItem(FunctionCall(x)) for x in decls]



# endregion



















class Kbdbg(Node):
	def __init__(s):
		super(Kbdbg, s).__init__()
		s.isroot = True
		s.parent = None
		s.decl = None
		s.delayed_cursor_move = DelayedCursorMove()
		s.indent_length = 4
		s.changed = True
		s.brackets = ("", "")
		s.items = []
		s.arrows = []
		s.loadkb()
		print (Kbdbg.keys)
		s.update()

	def render(s):
		yield ColorTag(colors.fg)
		print ("RENDER")
		yield s.items
		yield EndTag()

	def update(s):
		#for a in s.arrows:
			#print (a)
		print ("UPDATE")
			
		s.items.clear()
		for i in s.kb:
			#print(i.markup)
			if len(i.markup) != 0:
				for a in s.arrows:
					if i.markup == a[0]["markup"]:
						#print ("OOO", i.markup, "FFF", a[0]["markup"])
						for j in s.kb:
							#print("XXX",  j.markup, a[1]["markup"])
							if j.markup == a[1]["markup"]:
								style = a[2]
								s.items.append(ArrowTag(j, style))
								s.items.append("o")
					#if i.markup == a[1]["markup"]:
					#	s.items.append("x")
	

			s.items.append(ElementTag(i))
	
	def add_step(s):
		print("adding step")
		s.steps.append(Dotdict())
		s.steps[-1].log = []
		s.steps[-1].vis = []

	def loadkb(s):

		s.steps = []
		s.add_step()
		input = json.load(open("kbdbg.json", "r"))
		s.kb = []
		for i in input:
			if isinstance(i, dict):
				#print (i)
				if i["type"] == "step":
					s.add_step()
				else:
					s.steps[-1].vis.append(i)
			elif isinstance(i, unicode):
				s.steps[-1].log.append(i)
			elif isinstance(i, list):
				for x in i:
					if isinstance(x, str):
						t = x
						m = []
					elif isinstance(x, dict):			
						t = x["text"]
						m = x["markup"]
					w = widgets.Text(s, t)		
					w.markup = m
					s.kb.append(w)

		s.arrows = []
		s.cache = {}
		s.step = -1
		s.step_fwd()

	def print_log(s):
		for line in s.steps[s.step].log:
			print(line)

	def step_back(s):
		
		if s.step != 0:
			s.step -= 1
		s.arrows = copy(s.cache[s.step])
		s.update()
		if s.step == 0:
			print()
			print()
			print()
			print()
			print("START")
			print()
			print()
			print()
			
		print ("step:", s.step)
		s.print_log()

	def step_fwd(s):
		
		if s.step < len(s.steps) -1 :
			s.step += 1
			if s.step in s.cache:
				s.arrows = copy(s.cache[s.step])
			else:
				s.do_step(s.step)
				s.cache[s.step] = copy(s.arrows)
			s.update()
		print ("step:", s.step)
		s.print_log()

	def do_step(s, i):
	
		for x in s.steps[i].vis:
			print(x)
			p = (x["a"], x["b"], x["style"])
			if x["type"] == "add":
				print("add" , p)
				s.arrows.append(p)
			elif x["type"] == "remove":
				for y in range(len(s.arrows)):
					if s.arrows[y] == p:
						print("remove" , p)
						s.arrows.remove(p)
						break
			else:
				assert(False)


	def has_result(s):
		for line in s.steps[s.step].log:
			if line[:6] == "RESULT":
				return True


	def res_back(s,e):
		while s.step != 0:
			s.step_back()
			if s.has_result(): return
	
	def res_fwd(s,e):
		while s.step < len(s.steps) -1 :
			s.step_fwd()
			if s.has_result(): return
			

		



		




def make_root():
	if args.kbdbg:
		return Kbdbg()
		
		
		
		

	r = Root()

	build_in_editor_structure_nodes()
	build_in_lemon_language()
	build_in_misc()

	#for k,v in iteritems(B._dict):
	#	log(k, v)


	r['welcome'] = Comment("Press F1 to cycle the sidebar!")
	r["intro"] = new_module()
	r["intro"].ch.statements.items = [
		Comment("""

the interface of lemon is currently implemented like this:
root is a dictionary with keys like "intro", "some program" etc.
it's values are mostly modules. modules can be collapsed and expanded and they
hold some code or other stuff in a Statements object. This is a text literal inside a module, too.

Lemon can't do much yet. You can add function calls and maybe define functions. If you are lucky,
ctrl-del will delete something. Inserting of nodes happens in the Parser node."""),
		#it looks like this:"""),
		#Parser(b['number']), todo:ParserWithType
		Comment("If cursor is on a parser, a menu will appear in the sidebar. you can scroll and click it. have fun."),
		Comment("todo: working editor, smarter menu, better parser, real language, fancy projections...;)")
	]





	r["intro"].ch.statements.view_mode=0
	#r.add(("lesh", Lesh()))
	r["some program"] = new_module()
	r["some program"].ch.statements.newline()
	r["some program"].ch.statements.view_mode=0
	#r['some program'].ch.statements.items[1].add("12")
	#r["lemon console"] =b['module'].inst_fresh()

	r["loaded program"] = B.module.inst_fresh()
	r["loaded program"].ch.name = Text("placeholder")
	r["loaded program"].ch.statements.view_mode=0

	library = r["library"] = make_list('module')
	library.view_mode = 0#library.vm_multiline


	r["builtins"] = new_module()
	r["builtins"].ch.statements.items = list(itervalues(B._dict))
	assert len(r["builtins"].ch.statements.items) == len(B) and len(B) > 0
	log("built in %s nodes",len(r["builtins"].ch.statements.items))
	r["builtins"].ch.statements.add(Comment("---end of builtins---"))
	r["builtins"].ch.statements.view_mode = 0













	
	build_in_lc1(r)
	build_in_lc2(r)
	build_in_cube(r)








	import glob
	for file in glob.glob("library/*.lemon.json"):
		placeholder = library.add(new_module())
		placeholder.ch.name.pyval = "placeholder for "+file
		load_module(file, placeholder)
	#todo: walk thru weakrefs to serialized, count successful deserializations, if > 0 repeat?



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
	build_in(Nodecl(Comment))
	build_in(TypeNodecl(), 'type')

	build_in(
	ParametricNodecl(ParametricListType,
					 [TextTag("list of"), ChildTag("itemtype")],
					 {'itemtype': B.type}),'list')

	build_in(
	SyntaxedNodecl(Definition,
				   [TextTag("define"), ChildTag("name"), TextTag("as"), ChildTag("type")], #expression?
				   {'name': 'text', 'type': 'type'}))


	build_in(
		SyntaxedNodecl(SyntacticCategory,
			[TextTag("syntactic category:"), ChildTag("name")],
			{'name': 'text'}))

	build_in(SyntacticCategory({'name': Text("statement")}))
	build_in(SyntacticCategory({'name': Text("anything")}))

	build_in(
		Definition(
			{'name': Text("list of anything"),
			 'type': list_of(B.anything)}))

	build_in(Nodecl(Statements))

	build_in(
	SyntaxedNodecl(Module,
				   ["module", ChildTag("name"), 'from', ChildTag("file"), ":\n", ChildTag("statements"),  TextTag("end.")],
				   {'statements': B.statements,
				    'name': B.text,
				    'file': B.text
				    }))

def build_in_lemon_language():

	build_in(Comment(
	"""We start by declaring the existence of some types (decls).
	Once declared, we can reference them from lemon objects.
	Internally, each declaration is a Nodecl object.
	The type name is usually a lowercased
	name of the python class that implements it."""))


	build_in(VarRefNodecl(), 'varref')

	build_in([Nodecl(x) for x in [Number, Banana, Bananas, Identifier, RestrictedIdentifier]])

	build_in(Nodecl(List), "list_literal")

	build_in([
		SyntaxedNodecl(WorksAs,
					   [ChildTag("sub"), TextTag(" works as "), ChildTag("sup")],
					   {'sub': 'type', 'sup': 'type'}),

		SyntacticCategory({'name': Text("expression")})
	])

	build_in(WorksAs.b("statement", "anything"), False)
	build_in(WorksAs.b("expression", "statement"), False)
	build_in(WorksAs.b("number", "expression"), False)
	build_in(WorksAs.b("text", "expression"), False)


	build_in(
	ParametricNodecl(ParametricDictType,
					 [TextTag("dict from"), ChildTag("keytype"), TextTag("to"), ChildTag("valtype")],
					 {'keytype': B.type, 'valtype': B.type}), 'dict')

	build_in(WorksAs.b("list", "expression"), False)
	#build_in(WorksAs.b("dict", "expression"), False)



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
			 'type': list_of(B.type)}))

	build_in(SyntaxedNodecl(Union,
				   [TextTag("union of"), ChildTag("items")],
				   {'items': list_of(B.type)}))
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
					    list_of(B.anything)#?
					    ),
				   'body': B.statements}))


	build_in(SyntaxedNodecl(VarlessFor,
				   [TextTag("for"), ChildTag("items"),
				        ":\n", ChildTag("body")],
				   {'items': Exp(list_of('anything')),
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
	tmp = list_of(B.function_signature_node)
	build_in(Definition({'name': Text('function signature list'), 'type':tmp}))
	#todo:refactor
	#and a custom node syntax type
	tmp = B.union.inst_fresh()
	tmp.ch["items"].add(Ref(B.text))
	tmp.ch["items"].add(Ref(B.type))
	build_in(Definition({'name': Text('custom syntax node'), 'type': tmp}))
	tmp = list_of(B.custom_syntax_node)
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
		print (o)
		#log(o)
		return NoValue()

	BuiltinFunctionDecl.create(
		"print",
		b_print,
		[ Text("print"), TypedParameter({'name': Text("expression"), 'type': Ref(B.expression)})])



	build_in(FunctionCallNodecl(), 'call')
	build_in(WorksAs.b("call", "expression"), False)




	def pfn(function, signature, return_type = int, **kwargs):
		"""helper function to add a builtin python function"""
		if return_type == int:
			return_type = Ref(B.number)
		elif return_type == bool:
			return_type = Ref(B.bool)
		elif return_type == str:
			return_type = Ref(B.text)
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
		pfn(op.add, [str_arg('A'), Text("+"), str_arg('B')], str, name='str add')
		pfn(op.eq,  [num_arg('A'), Text("=="),num_arg('B')], bool)
		pfn(op.ge,  [num_arg('A'), Text(">="),num_arg('B')], bool)
		pfn(op.gt,  [num_arg('A'), Text(">"), num_arg('B')], bool)
		pfn(op.le,  [num_arg('A'), Text("<="),num_arg('B')], bool)
		pfn(op.lt,  [num_arg('A'), Text("<"), num_arg('B')], bool)
		pfn(op.mod, [num_arg('A'), Text("%"), num_arg('B')])
		pfn(op.mul, [num_arg('A'), Text("*"), num_arg('B')])
		pfn(op.neg, [Text("-"), num_arg()])
		pfn(op.sub, [num_arg('A'), Text("-"), num_arg('B')])
		pfn(str,    [Text("str"), num_arg('converted')], str)

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

	build_in(Definition({'name': Text('lvalue'), 'type':make_union([Ref(B.identifier), Ref(B.varref)])}))

	"""
	types and unions make the world burn
	class Assignment(Syntaxed):
		pass
	build_in(SyntaxedNodecl(Assignment,
				   [ChildTag('target'), "=", ChildTag("source")],
				   {'target' : B.lvalue,
				   'source': B.expression}))
	"""



	class After(Syntaxed):
		pass
	#how to best choose the syntax from within a parent node?
	"""
	build_in(SyntaxedNodecl(After,
	                        ['after', ChildTag('function'), ':\n', ChildTag('body')],
		{'function': B.functionsignatureref,
		 'body': B.statements}))
	"""


class Serialized(Syntaxed):
	def __init__(s, children):
		#s.status = widgets.Text(s, "(status)")
		#s.status.color = "compiler hint"
		super(Serialized, s).__init__(children)

	def _eval(s):
		return Banana("deserialize me first")

	def on_keypress(s, e):
		if e.key == K_d and e.mod & KMOD_CTRL:
			s.unserialize()
			return True

	def unserialize(s):
		data = s.ch.serialization.pyval
		log("unserializing %s"%data)
		new = deserialize(data, s)
		log("voila:%s"%new)
		s.parent.replace_child(s, new)



def b_lemon_load_file(root, name):
	return load_module(name, root["loaded program"])

def load_module(file_name, placeholder):
	log("loading "+file_name)
	try:
		input = json.load(open(file_name, "r"))
	except Exception as e:
		return str(e)
	d = deserialize(input, placeholder)
	placeholder.parent.replace_child(placeholder, d)
	d.ch.file.pyval = file_name
	d.fix_parents()
	for i in d.flatten():
		if isinstance(i, Serialized):
			i.unserialize()
		d.fix_parents()
	log("ok")
	return file_name + " loaded ok"





def build_in_misc():
	class Note(Syntaxed):
		def __init__(s, children):
			#s.text = widgets.Text(s, "")
			super(Note,s).__init__(children)

	build_in(SyntaxedNodecl(Note,
				   [["note: ", ChildTag("text")]],
				   {'text': B.text}))


	class Annotation(Node):
		def __init__(s, target, text):
			s.text = text
			s.target = target
			super(Annotation,s).__init__()

		def render(s):
			return [ArrowTag(s.target), TextTag(s.text)]


	class Clock(Node):
		def __init__(s):
			super(Clock,s).__init__()
			s.datetime = __import__("datetime")
		def render(s):
			return [TextTag(str(s.datetime.datetime.now()))]
		def _eval(s):
			return Text(str(s.datetime.datetime.now()))



	class PythonEval(Syntaxed):
		def __init__(s, children):
			super(PythonEval, s).__init__(children)

	SyntaxedNodecl(PythonEval,
				   [TextTag("python eval"), ChildTag("text")],
				   {'text': Exp(B.text)})



	class ShellCommand(Syntaxed):
		info = ["runs a command with os.system"]
		def __init__(s, children):
			super(ShellCommand, s).__init__(children)

		def _eval(s):
			cmd = s.ch.command.eval().pyval
			import subprocess
			try:
				o = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
			except subprocess.CalledProcessError as e:
				o = e.output

			return Text(str(o))

	build_in(SyntaxedNodecl(ShellCommand,
				   [["bash:", ChildTag("command")]],
				   {'command': Exp(B.text)}))


	class FilesystemPath(Syntaxed):
		def __init__(s, children):
			s.status = widgets.Text(s, "(status)")
			s.status.color = colors.parser_hint
			super(FilesystemPath, s).__init__(children)

		def _eval(s):
			p = s.ch.path.eval().pyval
			from os import path
			s.status.text = "(valid)" if path.exists(p) else "(invalid)"
			return Text(p)


	build_in(SyntaxedNodecl(FilesystemPath,
				   [[ChildTag("path")],
				    [ChildTag("path"), MemberTag("status")]],
				   {'path': (B.text)}))

	def b_files_in_dir(dir):
		import os
		for x in os.walk(dir):
			return x[2]
		return []

	BuiltinPythonFunctionDecl.create(b_files_in_dir, [Text("files in"), str_arg()], list_of('text'), "list files in dir", "ls, dir")

	BuiltinPythonFunctionDecl.create(
		b_lemon_load_file, [Text("load"), str_arg()], Ref(B.text), "load file", "open").pass_root = True


#BuiltinMenuItem..


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


lc1 = Dotdict() #a helper dict to hold the nodes being built in and to reference them easily
lc1._dict = odict()


#interesting vim glitch made it look like it was commented out
#if i search "/def build_in_lc(" from the top, i guess it doesn't
#parse the whole file but sees this \"\"\" above
#scroll up and back down and it goes away
def build_in_lc1(r):
	"""creates a new module with definitions for a language separate from
	the lemon stuff
	eventually, this would all be just data in lemon,
	but for now, we "build it in"
	"""
	

	r["lc1"] = new_module()
	r["lc1"].ch.statements.items = [
		Comment("""untyped lambda calculus""")]

	""" whats the lc1-test for """
	#well the gui shows a "root", a tree with a couple of entries,
	#so thats like where you would type in your lambda calculus program	
	r["lc1-test"] = new_module()
	r["lc1-test"].special_scope = [r["lc1"], 
		#B.restrictedidentifier#i will remove this once Syntaxed parser is done, its only to pull in the grammar
		];
		
		

	build_in(SyntacticCategory({'name': Text("exp")}), None, lc1)
	lc1.exp.help = ["a lambda expression"]
	

	class Var(Syntaxed):
		brackets = ("", "")
		help = ["a variable"]
		@property
		def varName(s):
			return s.ch.name.pyval
		@varName.setter
		def varName(s, v):
			s.ch.name.pyval = v
		
	build_in(SyntaxedNodecl(Var,
		[ChildTag("name")],
		{'name': B.restrictedidentifier}), None, lc1)
	#what's B.identifier
	#like we use the lc1 here, B is the main global builtins
	#ah, and i guess identifier is just what we want a name to be?yea

	lc1.var.example = lc1.var.inst_fresh()
	lc1.var.example.ch.name.text = "x"



	class ParExp(Syntaxed): 
		help = ["a parenthesized expression"]
		brackets = ("", "")
		
	build_in(SyntaxedNodecl(ParExp,
		[TextTag("("), ChildTag("exp"), TextTag(")")],
		{'exp': lc1.exp}), None, lc1)
	build_in(WorksAs.b(lc1.parexp, lc1.exp), False, lc1)



	class Abs(Syntaxed): 
		help = ["abstraction, a lambda"]
		#def eval(s):
		
		
		
	build_in(SyntaxedNodecl(Abs,
		[TextTag("\\"), ChildTag("var"), TextTag("."), ChildTag("exp")],
		{'var': lc1.var, 'exp': lc1.exp}), None, lc1)




	class App(Syntaxed): 
		help = ["function application, a call"]
		pass
	build_in(SyntaxedNodecl(App,
		[ChildTag("e1"), TextTag(" "), ChildTag("e2")],
		{'e1': lc1.exp, 'e2': lc1.exp}), None, lc1)


	build_in(WorksAs.b(lc1.app, lc1.exp), False, lc1)
	build_in(WorksAs.b(lc1.abs, lc1.exp), False, lc1)
	build_in(WorksAs.b(lc1.var, lc1.exp), False, lc1)


	r["lc1"].ch.statements.items.extend(list(itervalues(lc1._dict)))
	




	Var.unparen = lambda s: s
	App.unparen = Abs.unparen = lambda s: s.__class__(dict([(k, v.unparen()) for k, v in iteritems(s.ch._dict)]))
	ParExp.unparen = lambda s: s.ch.exp.unparen()
	
	
	#//aka evaluate
	#//Normal order:
	def normalize (e) :
		if isinstance(e, Var):
			return e
			
		if isinstance(e, Abs):
			#return Abs({'var': e.ch.var.copy(), e.ch.exp.eval()})
			return Abs({'var': e.ch.var, 'exp': e.ch.exp.eval()})
			
		if isinstance(e, App):
			if isinstance(e.ch.e1, Abs):
				#//one-step evaluation:
				
				#return subst(e.ch.e1.ch.e2, e.ch.e1.ch.e1, e.ch.e2)
				return subst(e.ch.e1.ch.exp, e.ch.e1.ch.var, e.ch.e2)
				
				#//full evaluation:
				#return subst(e3,x,e2).eval()
				#return subst(e.ch.e1.ch.exp, e.ch.e1.ch.var, e.ch.e2).eval()
				
			if isinstance(e.ch.e1, App):
				#//one step eval or no-op
				tmp = e.ch.e1.eval()
				return App({'e1': tmp, 'e2' : e.ch.e2})
				
				#//definite one step evaluation:
				#not a no-op unless it's in normal form
				#tmp = e.ch.e1.eval()
				#if(tmp == e.ch.e1)
				#	return App({'e1': e.ch.e1, 'e2': e.ch.e2.eval()})
				#else
				#	return App({'e1': tmp, 'e2': e.ch.e2})
				
				
				#//full evaluation:
				#tmp = e.ch.e1.eval()
				
				#only run subst if tmp is an Abs
				
				#if isinstance(tmp, Abs):
				#	return subst(tmp.ch.exp,tmp.ch.var,e.ch.e2).eval()
				#else
				#	return App({'e1': tmp, 'e2': e.ch.e2.eval()})
					
			return e
		assert False, "normalize"


	def eval(e):
		x = e.copy().unparen()
		print (x.tostr())
		n = normalize(x)
		assert n
		return n.copy()

	ParExp.eval = App.eval = Abs.eval = Var.eval = eval


	freshvarid = [0]
	def genFreshVarName():
		freshvarid[0] += 1
		return "var" + freshvarid[0]


	def subst( where, what:Var, by):#e1,x,e2):
		print ("subst where", where.tostr(), "what", what.tostr(), "by", by.tostr())
		if isinstance(where, Var):
			#(Var x)[x := r]         = r
			if (where.varName == what.varName):
				return by
			#(Var y)[x := r]         = y 
			#i'm thinking more like this case
			else:
				return where
		if isinstance(where, App):
			#(App t s)[x := r]       = (t[x:=r])(s[x:=r])
			return App({'e1': subst(where.ch.e1, what, by), 'e2': subst(where.ch.e2, what, by)})
		if isinstance(where, Abs):
			#(Abs x t)[x := r]       = (Abs x t).
			#i think this should be where.ch.var.varName?
			#ah, yea
			# guess we never called an example that used it
			#name would be "RestrictedIdentifier" i think
			#i'm actually still a bit confused about this
			#case myself, but it's what the capture-avoiding
			#substitution rules say to do, *shrug*
			if(where.ch.var.varName == what.varName):
				print ("where is what so fuck you")
			#this would happen in a case like:
			#(\x.(\x.x)) y
			#to evaluate this we're gonna "replace all
			#occurences of 'x' in (\x.x) with 'y'"
			#but i guess the inner \x is taken to be
			# a different var than the outer \x
			
				return where
			else:
				#(Abs y t)[x := r]                                                                
				#if(y not in FreeVars(r))
				
				print("where.var:", where.ch.var.varName, "FreeVars(by):",FreeVars(by))
				if(where.ch.var.varName not in FreeVars(by)):
					print ("var not in freevars")
					#(Abs y subst(t,x,r))
					return Abs({'var':where.ch.var, 'exp': subst(where.ch.exp, what, by)}) 
				else:
					print ("var in freevars")
					z = genFreshVarName()

					#t' = subst(t,y,z)
					t1 = subst(where.ch.exp,where.ch.var,z)

					#t'' = subst(t',x,r)
					t2 = subst(t1,what,by)

					#return (Abs z t'')
					return Abs({'var': z, 'exp': t2})
		assert False, ("subst", where, what, by)
		
		
	
	def FreeVars(expr,vars=None) -> set:
		#shall we save varNames only?
		#we could do that, name is all the structure they have
		#otherwise this set magic wont work so magically
		#standard implementations would do something like
		#de bruijn indexes, i.e. just replace them with numbers

		if vars==None: vars = set()
		print("freevars", expr.tostr(), "vars:", vars)
		
		if isinstance(expr,Var):
			vars.add(expr.varName)
			return vars

		#if (e is a Abs var exp)
		if isinstance(expr,Abs):
			free = FreeVars(expr.ch.exp, vars)
			free.remove(expr.ch.var.varName)#because it's bound by this abstraction
			#how would it be bound by the abstraction if it didnt actually appear in the body?
			#well, *if* it appears in the body then we remove it but i hope this
			#set routine already handles that
			return free
		#if (e is a App e1 e2)
		if isinstance(expr,App):
			free_e1 = FreeVars(e1, vars)
			free_e2 = FreeVars(e2, vars)
			return free_e1.union(free_e2)
#a var X appearing in an expression is free, 
#unless it is used in the .ch.exp of an abstraction
#whose .ch.var is that var, unless unless the expression
#is an application and X is free in the other half
#hrm good point, lemme see what the wiki says

#"The set of free variables of (a b) is the union of the set
#of free variables of a and the set of free variables of b"

lc2 = Dotdict() 
lc2._dict = odict()
def build_in_lc2(r):
	r["lc2"] = new_module()
	r["lc2"].ch.statements.items = [
		Comment("""simply typed lambda calculus""")]

	r["lc2-test"] = new_module()
	r["lc2-test"].special_scope = [r["lc2"], B.number];
		
	

	build_in(SyntacticCategory({'name': Text("exp")}), None, lc2)
	lc2.exp.help = ["a lambda expression"]
	

	class Var(Syntaxed):
		brackets = ("", "")
		help = ["a variable"]
		@property
		def varName(s):
			return s.ch.name.pyval
		@varName.setter
		def varName(s, v):
			s.ch.name.pyval = v
		
	build_in(SyntaxedNodecl(Var,
		[ChildTag("name")],
		{'name': B.restrictedidentifier}), None, lc2)

	class ParExp(Syntaxed): 
		help = ["a parenthesized expression"]
		brackets = ("", "")
		
	build_in(SyntaxedNodecl(ParExp,
		[TextTag("("), ChildTag("exp"), TextTag(")")],
		{'exp': lc2.exp}), None, lc2)
	build_in(WorksAs.b(lc2.parexp, lc2.exp), False, lc2)


	build_in(SyntacticCategory({'name': Text('type')}), None, lc2)

	class ParType(Syntaxed): 
		help = ["a parenthesized type"]
		brackets = ("", "")
	build_in(SyntaxedNodecl(ParType,
		[TextTag("("), ChildTag("type"), TextTag(")")],
		{'type': lc2.type}), None, lc2)
	build_in(WorksAs.b(lc2.partype, lc2.type), False, lc2)


	class FunType(Syntaxed): 
		help = ["function type"]
	build_in(SyntaxedNodecl(FunType,
		[
		[ChildTag("from"), TextTag("->"), ChildTag("to")],
		["function from ", ChildTag("from"), " to ", ChildTag("to")]],
		{'from': lc2.type, 'to': lc2.type}), None, lc2)
	build_in(WorksAs.b(lc2.funtype, lc2.type), False, lc2)

	class IntType(Syntaxed): 
		help = ["integer type"]
	build_in(SyntaxedNodecl(IntType,
		[TextTag("int")],
		{}), None, lc2)
	class BoolType(Syntaxed): 
		help = ["bool type"]
	build_in(SyntaxedNodecl(BoolType,
		[TextTag("bool")],
		{}), None, lc2)


	build_in(SyntacticCategory({'name': Text('basetype')}), None, lc2)
	build_in(WorksAs.b(lc2.basetype, lc2.type), False, lc2)
	build_in(WorksAs.b(lc2.booltype, lc2.basetype), False, lc2)
	build_in(WorksAs.b(lc2.inttype,  lc2.basetype), False, lc2)



	build_in(SyntacticCategory({'name': Text('constant')}), None, lc2)
	build_in(SyntacticCategory({'name': Text('bool')}), None, lc2)
	build_in(WorksAs.b(lc2.bool, lc2.constant), False, lc2)
	build_in(WorksAs.b(B.number,  lc2.constant), False, lc2)
	build_in(WorksAs.b(lc2.constant, lc2.exp), False, lc2)



	class BoolTrue(Syntaxed): 
		help = ["..."]
	build_in(SyntaxedNodecl(BoolTrue,
		[TextTag("true!")],
		{}), None, lc2)
	build_in(WorksAs.b(lc2.booltrue, lc2.bool), False, lc2)
	class BoolFalse(Syntaxed): 
		help = ["..."]
	build_in(SyntaxedNodecl(BoolFalse,
		[TextTag("false!")],
		{}), None, lc2)
	build_in(WorksAs.b(lc2.boolfalse, lc2.bool), False, lc2)




	"""
Type := FunType | BaseType
FunType := Type -> Type
BaseType := "Int" | "Bool"
Constant := Number | Bool

ParType := "(" Type ")"
Type := ParType
ParExpr := "(" Expr ")"

Expr := Var | Abs | App | Constant
Var := Identifier
Abs := "\\" Var ":" Type "." Expr
App := Expr " " Expr
	"""

	
	class Abs(Syntaxed): 
		help = ["abstraction, a lambda"]
		
	build_in(SyntaxedNodecl(Abs,
		[[TextTag("\\"), ChildTag("var"), TextTag(":"), ChildTag("type"), TextTag("."), ChildTag("exp")],
		[TextTag("function taking ("), ChildTag("var"), TextTag(" - a "), ChildTag("type"), TextTag("):"), IndentTag(),"\n",  ChildTag("exp"), DedentTag(), "\n"]],
		{'var': lc2.var, 'type': lc2.type, 'exp': lc2.exp}), None, lc2)



	#"do" <function> "to" <argument>
	#"run" <function> "on" <argument>
	class App(Syntaxed): 
		help = ["function application, a call"]
		
	build_in(SyntaxedNodecl(App,
		[[ChildTag("e1"), TextTag(" "), ChildTag("e2")],
		[ChildTag("e1"), TextTag(" applied to "), ChildTag("e2")]],
		{'e1': lc2.exp, 'e2': lc2.exp}), None, lc2)

	for x in [App, Abs, FunType]: x.default_syntax_index = 1

	build_in(WorksAs.b(lc2.app, lc2.exp), False, lc2)
	build_in(WorksAs.b(lc2.abs, lc2.exp), False, lc2)
	build_in(WorksAs.b(lc2.var, lc2.exp), False, lc2)


	r["lc2"].ch.statements.items.extend(list(itervalues(lc2._dict)))
	




	ParExp.unparen = lambda s: s.ch.exp.unparen()
	ParType.unparen = lambda s: s.ch.type.unparen()



	

	
	#//aka evaluate
	#//Normal order:
	def normalize (e) :
		if type(e) in [BoolTrue, BoolFalse, Number]:
			return e
		if isinstance(e, Var):
			#yea this isnt the top-level-only normalize()
			#print("Your type-checking sucks")
			#assert False
			return e
			
		if isinstance(e, Abs):
			#return Abs({'var': e.ch.var.copy(), e.ch.exp.eval()})
			return Abs({'var': e.ch.var, 'type': e.ch.type, 'exp': e.ch.exp.eval()})
			
		if isinstance(e, App):
			if isinstance(e.ch.e1, Abs):
				#//one-step evaluation:
				
				#return subst(e.ch.e1.ch.e2, e.ch.e1.ch.e1, e.ch.e2)
				#return subst(e.ch.e1.ch.exp, e.ch.e1.ch.var, e.ch.e2)
				
				#//full evaluation:
				#return subst(e3,x,e2).eval()
				return subst(e.ch.e1.ch.exp, e.ch.e1.ch.var, e.ch.e2).eval()
				
			if isinstance(e.ch.e1, App):
				#//one step eval or no-op
				#tmp = e.ch.e1.eval()
				#return App({'e1': tmp, 'e2' : e.ch.e2})
				
				#//definite one step evaluation:
				#not a no-op unless it's in normal form
				#tmp = e.ch.e1.eval()
				#if(tmp == e.ch.e1)
				#	return App({'e1': e.ch.e1, 'e2': e.ch.e2.eval()})
				#else
				#	return App({'e1': tmp, 'e2': e.ch.e2})
				
				
				#//full evaluation:
				tmp = e.ch.e1.eval()
				
				#only run subst if tmp is an Abs
				
				if isinstance(tmp, Abs):
					return subst(tmp.ch.exp,tmp.ch.var,e.ch.e2).eval()
				else:
					print("Your type-checking sucks")
					assert false
					#return App({'e1': tmp, 'e2': e.ch.e2.eval()})
					
			return e
		assert False, "normalize"


	def eval(e):
		x = e.copy().unparen()
		print (x.tostr())
		n = normalize(x)
		assert n
		return n.copy()

	ParExp.eval = App.eval = Abs.eval = Var.eval = eval



#?
	for x in [BoolTrue, BoolFalse]:
		x._eval = lambda s:s.copy()



	freshvarid = [0]
	def genFreshVarName():
		freshvarid[0] += 1
		return "var" + freshvarid[0]


	def subst( where, what:Var, by):#e1,x,e2):
		print ("subst where", where.tostr(), "what", what.tostr(), "by", by.tostr())
		if type(where) in [BoolTrue, BoolFalse, Number]:
			return where
		if isinstance(where, Var):
			#(Var x)[x := r]         = r
			if (where.varName == what.varName):
				return by
			#(Var y)[x := r]         = y 
			#i'm thinking more like this case
			else:
				return where
		if isinstance(where, App):
			#(App t s)[x := r]       = (t[x:=r])(s[x:=r])
			
			#right, what type?
			#types are irrelevant by the time we get to eval
			return App({'e1': subst(where.ch.e1, what, by), 'e2': subst(where.ch.e2, what, by)})
		if isinstance(where, Abs):
			#(Abs x t)[x := r]       = (Abs x t).
			#i think this should be where.ch.var.varName?
			#ah, yea
			# guess we never called an example that used it
			#name would be "RestrictedIdentifier" i think
			#i'm actually still a bit confused about this
			#case myself, but it's what the capture-avoiding
			#substitution rules say to do, *shrug*
			if(where.ch.var.varName == what.varName):
				print ("where is what so fuck you")
			#this would happen in a case like:
			#(\x.(\x.x)) y
			#to evaluate this we're gonna "replace all
			#occurences of 'x' in (\x.x) with 'y'"
			#but i guess the inner \x is taken to be
			# a different var than the outer \x
			
				return where
			else:
				#(Abs y t)[x := r]                                                                
				#if(y not in FreeVars(r))
				
				print("where.var:", where.ch.var.varName, "FreeVars(by):",FreeVars(by))
				if(where.ch.var.varName not in FreeVars(by)):
					print ("var not in freevars")
					#(Abs y subst(t,x,r))
					#i guess not completely irrelevant
					return Abs({'var':where.ch.var, 'type': where.ch.type, 'exp': subst(where.ch.exp, what, by)}) 
				else:
					print ("var in freevars")
					z = genFreshVarName()

					#t' = subst(t,y,z)
					t1 = subst(where.ch.exp,where.ch.var,z)

					#t'' = subst(t',x,r)
					t2 = subst(t1,what,by)

					#return (Abs z t'')
					return Abs({'var': z, 'type': where.ch.type, 'exp': t2})
		assert False, ("subst", where, what, by)
		
		
	
	def FreeVars(expr,vars=None) -> set:
		#shall we save varNames only?
		#we could do that, name is all the structure they have
		#otherwise this set magic wont work so magically
		#standard implementations would do something like
		#de bruijn indexes, i.e. just replace them with numbers

		if vars==None: vars = set()
		print("freevars", expr.tostr(), "vars:", vars)
		if type(expr) in [BoolTrue, BoolFalse, Number]:
			return vars
		if isinstance(expr,Var):
			vars.add(expr.varName)
			return vars

		#if (e is a Abs var exp)
		if isinstance(expr,Abs):
			free = FreeVars(expr.ch.exp, vars)
			free.remove(expr.ch.var.varName)#because it's bound by this abstraction
			#how would it be bound by the abstraction if it didnt actually appear in the body?
			#well, *if* it appears in the body then we remove it but i hope this
			#set routine already handles that
			return free
		#if (e is a App e1 e2)
		if isinstance(expr,App):
			free_e1 = FreeVars(e1, vars)
			free_e2 = FreeVars(e2, vars)
			return free_e1.union(free_e2)

		assert None, expr
#a var X appearing in an expression is free, 
#unless it is used in the .ch.exp of an abstraction
#whose .ch.var is that var, unless unless the expression
#is an application and X is free in the other half
#hrm good point, lemme see what the wiki says

#"The set of free variables of (a b) is the union of the set
#of free variables of a and the set of free variables of b"

	#so we call type_check with the expression
	#to be type-checked and a list of "type-assumptions"
	
	#for the top-level expression that we intend to
	#evaluate, we'll be calling this with the default,
	#i.e. an empty set of type-assumptions.
	
	#the set of type-assumptions is a map from vars
	#to their types
	def type_check(expr,env=None):
		if env==None: env = {}
		#so if our 'e' was a Var, then we're
		#just gonna grab it's type-assumption
		#from the list
		
		#if the type-assumption isn't there, then
		#we'll get a KeyError, which is fine cause
		#we're supposed to fail anyway in that case
		
		#if the type-assumption isn't there, then
		#it's basically like i just give you:
		
		# "x"
		#and ask you what's the type
		#there's no answer to that, it's untyped
		if isinstance(expr,Var):
			return env[expr.varName]
			"""
			check if expr is in env
			if so return the type associated
			with it, otherwise fail
			(if it's not there then python
			will fail for us, i hope)
		
			all vars must have a type-assumption
			by the time we get to them.
			type assumptions are given by abstractions,
			i.e. if we have '\\x:t.e', then when we go to
			type-check 'e', then env will contain 'x:t'
			"""
		#type-assumptions get added to the list from
		#abstractions
		
		#\\x:t.e, <-- "x:t" is a type-assumption
		#we'll add this type assumption to the list
		#before checking "e". 
		if isinstance(expr,Abs):
			#copy our current list of type-assumptions
			tmp_env = dict(env)
			
			#add the type assumption
			#if it's a repeated occurrence of a
			#var in an inner lambda like
			#\x:bool.\x:bool.x, then the inner
			#should shadow the outer
			
			#actually for a real lang we would
			#probably want to just disallow that
			#syntactically hrrm
			
			#\x:bool.\x:int.x
			#which x are we referring to?
			#the inner:p
			#our type-assumption will be the
			#inner one, that's ensured by this
			#next line, but how about for
			#normalization, substitution, etc?
			
			#so normalize doesnt deal with this as expected?
			#well, i think it's more that "expected" isnt
			#even really well-defined yet (for us)
			#well..lexical scope, i.e. the inner should
			#shadow the outer?yea ok we'll check over it in
			#a minute
			
			#it's not a big deal though, we
			#can just avoid those for now and
			#nit-pick at it later
			tmp_env[expr.ch.var.varName] = expr.ch.type
			return FunType({
				#this is just 't'
				"from": expr.ch.type,
				#\\x:t.e
				#so here we're type-checking the 'e'
				#using the new set of type-assumptions
				"to": type_check(expr.ch.exp,tmp_env)
				})
			#alright i think thats clear
			
		if isinstance(expr,App):
			func_t = type_check(expr.ch.e1, env)
			if isinstance(func_t,FunType):
				arg_t = type_check(expr.ch.e2, env)
				if arg_t.eq_by_value_and_python_class(func_t.ch._dict["from"]):
					return func_t.ch.to
				else:
					print("Bad argument type")
					assert False
			else:
				print("Application using non-function-type")
				assert False

		if type(expr) in [BoolTrue, BoolFalse]:
			return BoolType({})
		if isinstance(expr, Number):
			return IntType({})
		assert False
		#ok!
		#cool, make sense now?yeah thx np
		#and that's it, simply typed is done
		
		#ok time for a break i guess
	def tc(e):
		x = e.copy().unparen()
		print (x.tostr())
		n = type_check(x)
		assert n
		return n.copy()

		
	for x in [Var, App, Abs]:
		x.type_check = tc
		












"""
    	 _________________________
        / _____________________  /|
       / / ___________________/ / |
      / / /| |               / /  |
     / / / | |              / / . |
    / / /| | |             / / /| |
   / / / | | |            / / / | |
  / / /  | | |           / / /| | |
 / /_/__________________/ / / | | |
/________________________/ /  | | |
| ______________________ | |  | | |
| | |    | | |_________| | |__| | |
| | |    | |___________| | |____| |
| | |   / / ___________| | |_  / /
| | |  / / /           | | |/ / /
| | | / / /            | | | / /
| | |/ / /             | | |/ /
| | | / /              | | ' /
| | |/_/_______________| |  /
| |____________________| | /
|________________________|/

"""








cube = Dotdict() #a helper dict to hold the nodes being built in and to refe
cube._dict = odict()


def build_in_cube(r):
	r["cube"] = new_module()
	r["cube"].ch.statements.items = [
		Comment("""The lambda cube""")]

	r["cube-test"] = new_module()
	r["cube-test"].special_scope = [
		r["cube"]
		#B.number
	];
	
	build_in(SyntacticCategory({'name': Text("exp")}), None, cube)
	cube.exp.help = ["a lambda expression"]


	class Var(Syntaxed):
		brackets = ("", "")
		help = ["a variable"]
		@property
		def varName(s):
			return s.ch.name.pyval
		@varName.setter
		def varName(s, v):
			s.ch.name.pyval = v
		def __init__(s, children):
			super(Var, s).__init__(children)
			#if s.varName in ["box", 'star']:
				#assert False, s.varName
			#alright for now we'll take this assert out just to make sure we'll make it to the
			#parse we want
			#well it will kill the whole thing 
			#well...this approach isnt good in that we will have multiple parses, and processing some of those will abort
			#well..gets the job done?
#if we should discuss how this should be handled in lemon eventually, i dont know,
#i think in some cases we want the ambiguity...is all i know, i mean eventually in some big lemon lang
#ah sure, in a more extensive lang we might want to allow ambiguity in some cases
#for this though the only reason we have any ambiguity is because we have things as
#text instead of haskell inductive data types
#ill think about it some more, for now let's just avoid using any ambiguous examples
	build_in(SyntaxedNodecl(Var,
		[ChildTag("name")],
		{'name': B.restrictedidentifier}), None, cube)
	class ParExp(Syntaxed):
		help = ["a parenthesized expression"]
		brackets = ("", "")
	
	build_in(SyntaxedNodecl(ParExp,
		[TextTag("("), ChildTag("exp"), TextTag(")")],
		{'exp': cube.exp}), None, cube)
	build_in(WorksAs.b(cube.parexp, cube.exp), False, cube)
	
	class PiType(Syntaxed):
		help = ["""function type
		
		is this equivalent to FunType? whats the var there for?
		yea this is the new function type, it's actually a 
		generalization of function types: it's *dependent* function
		types, meaning the return type can depend on the input
		*value*, meaning the return type can be given as an
		expression in terms of the input value (which is what the
		var is there for)
		\\x:t -> (x -> x)
		so (x -> x) is a type of an identity function?
		the identity function for type x happens to be of type x -> x
		but there are other functions besides the identity function
		which have this as their type
		any function that takes an x and returns an x is of type x -> x
		sure
		this takes args of type 't', calls them 'x', and
		for any arg 'x', returns a value of type 'x->x'
		't' as in a type variable?
		
		well, this was a bad example because the only way
		i could actually do something like this is if i used
		* instead of t
		
		\\t : * . (t -> t)
		
		^ because i have to know that my 't' is a type in order
		to use "->" to construct a function/pi-type with it
		like, for example, \\x : bool . (x -> x) doesn't make
		any sense
		
		\\(arg)x:(type)t -> (ret)(x -> x)?
		right, and (ret) itself is a PiType
		\\_:x -> x
		\\arg:type -> ret
		  ^ this is just pretending it's quantified over the terms in
		  the type x, using some var "_" that doesn't appear in the
		  return type
		so..ret is an expression...
		not just ret but also type
		
		x -> x?
		hrm actually that's not a good example because "->" requires
		two types to construct another type
		
		need an example that uses terms to construct types
		the identity type works, but we don't really have this represented
		yet
		
		\\x:t -> (x ==_t x)
		
		this one makes sense whatever we use for 't', but you'll have
		to use your imagination a bit because we don't have anything like
		identity types implemented
		
		in fact afaict we don't have anything implemented that can take
		terms as arguments and construct types
		
		"->" is a 'type operator', it takes two *types* as arguments and
		returns a type, you can't necessarily pass it two *terms* and
		have it construct a meaningful function type, like
		\\x:bool -> (x -> x) doesn't make sense but
		\\t:* -> (t -> t) does make sense
		
		==_t otoh can take two terms of type t and construct a type from
		them
		
		
		function type is recovered as a special case of these
		namely a standard function type is any pi-type where
		the expression representing the return type doesn't
		depend on the input value
		
		\\x:bool -> int
		this is a function that takes args of type 'bool', refers
		to them as 'x', and returns an 'int'
		
		this looks like ret holds the type,
		while the x'es look like ret holds ..i dunno what, a type of an expression that you evaluate to get the return type
		
		
		
		
		"int" is a constant, it's not an expression in terms
		of "x", so this is equivalent to the standard
		function type "bool -> int"
		
		\\x:* -> (x -> int)
		
		the return type "(x -> int)" is an expression in terms of x
		
		
		
		
		maybe we should move onto some example code?
		so 'type' is an expression but not just any expression..
		
		
		
		
so, we cant have a function taking an argument of any type and returning it,
we need to basically pass it the type too? yea
allowing ourselves to range over our types (i.e. t:*) for the input of
our function is polymorphism, and we use it here to get a polymorphic identity
function, and yea making our functions polymorphic like this is handled by
basically extending their definition to take a type and return the desired
function/type/expression

and why cant we do \\x:*.x?
^this looks like given a value return a value?
a value of type *, aka a value of type Type, aka a type
so the 'type' field in Pi is the return type?
the input type, same as the 'type' field in the Abs
to be proper about it, we'd call it "domain", because it's
quite literally the domain of any function of that function-type

\\arg : domain -> range

err
yeah i see what you mean here, but
\\x:_.x
what about this identity function?
we don't have anything to allow this syntax
we don't even have anything to allow this syntax:
\\_:x. <something>
well, _ is a valid identifier name
hrm
or what about \\x:y.x
cant this be a function that just ignores y?
this function has type y -> y

so, if we had the := syntax, i could write
identity := \\x:y.x
and it would typecheck?
well, our type_check() function (which is really more of a type-inferencer
than a type-checker) would return a valid type for this
i.e. y -> y
if you had like haskell syntax:

identity :: y -> y
identity := \\x:y.x

then yea the function definition would type-check against the function
declaration

and y would be..what?
i'm just assuming here that "y" is just short-hand we're
using to express some specific (but unsaid) type
well i was thinking it would be i guess a variable

so it would kinda be a type variable
in the simply typed lambda and beyond, we can't realy
use a variable except inside a function
this also holds for type variables

\\t : * . (\\x : t . x)

okay
so, the argument type of a function 


we can but that's saying something different
namely: given any type, return this type
rather than, given any type, and a value of that type, return that value

		
		
		
		
		"""]
	build_in(SyntaxedNodecl(PiType,
		[
		[ChildTag("arg"), TextTag(":"), ChildTag("type"), TextTag("->"), ChildTag("ret")],
		#["function from ", ChildTag("from"), " to ", ChildTag("to")]
		],
		{'arg': cube.var, 'type': cube.exp, 'ret': cube.exp}), None, cube)
	
	class Abs(Syntaxed): 
		help = ["abstraction, a lambda"]
		#rank = -2000000
	build_in(SyntaxedNodecl(Abs,
		[[TextTag("\\"), ChildTag("var"), TextTag(":"), ChildTag("type"), TextTag("."), ChildTag("exp")],
		#[TextTag("function taking ("), ChildTag("var"), TextTag(" - a "), ChildTag("type"), TextTag("):"), IndentTag(),"\n",  ChildTag("exp"), DedentTag(), "\n"]
		],
		{'var': cube.var, 'type': cube.exp, 'exp': cube.exp}), None, cube)
	
	class App(Syntaxed): 
		#rank = 2000000
		help = ["""function application, a call
			#"do" <function> "to" <argument>
			#"run" <function> "on" <argument>
		"""]
		
	build_in(SyntaxedNodecl(App,
		[[ChildTag("e1"), TextTag(" "), ChildTag("e2")],
		#[ChildTag("e1"), TextTag(" applied to "), ChildTag("e2")]
		],
		{'e1': cube.exp, 'e2': cube.exp}), None, cube)
	
	
	class StarKind(Syntaxed):
		help = ["""star kind
		whats this?
		"""]
	build_in(SyntaxedNodecl(StarKind,
		[TextTag("*")], #[TextTag("*")],
		{}), None, cube)
		
	class BoxKind(Syntaxed): 
		help = ["""box kind
		whats this?
		"""]
	build_in(SyntaxedNodecl(BoxKind,
		[TextTag("box")], #[TextTag("[]")],
		{}), None, cube)
	
	build_in(SyntacticCategory({'name': Text("kind")}), None, cube)
	cube.kind.help = ["kind, like a type of types"]
	
	build_in(WorksAs.b(cube.starkind, cube.kind), False, cube)
	build_in(WorksAs.b(cube.boxkind, cube.kind), False, cube)
	
	
	
	#whoever came up with "pi", "box" and "star" must have had psychological problems
	#yes
	
	
	
	build_in(WorksAs.b(cube.app, cube.exp), False, cube)
	build_in(WorksAs.b(cube.abs, cube.exp), False, cube)
	build_in(WorksAs.b(cube.var, cube.exp), False, cube)
	build_in(WorksAs.b(cube.pitype, cube.exp), False, cube)
	build_in(WorksAs.b(cube.kind, cube.exp), False, cube)
	
	
	r["cube"].ch.statements.items.extend(list(itervalues(cube._dict)))
	
	
	def type_check(expr,env=None):
		#set up an empty list of type assumptions
		if (env == None) : env = {}
		
		#just like normally, we look up the type assumption for the variable
		#in the environment
		if isinstance(expr,Var):
			return env[expr.varName]
		
		
		if isinstance(expr,App):
			#type-check-reduce the function using the current
			#environment
			func_t = whnf(type_check(expr.ch.e1,env))
			
			#functions are supposed to have pi-types. we only
			#allow functions to appear in function-position in
			#applications. so make sure it's type is a pi-type:
			if isinstance(func_t, PiType):
				#if so, type-check the argument expression
				#using the current environment
				arg_t = type_check(expr.ch.e2,env)
				
				#so, we're expecting that the type of the bound
				#variable in the function could potentially be
				#expressed by the application of a type operator
				#or dependent type
				
				#(\x:((\t:*.t->t) int).x) (\x:int.5)
				
				#func_t := ((\t:*.t->t) int) -> ((\t:*.t->t) int)
				#arg_t := int->int 
				if (not (betaEq(func_t.ch.type,arg_t))):
					print("Error: bad argument type")
					assert False
				
				else:
					return subst(func_t.ch.ret, func_t.ch.arg, expr.ch.e2)
			
			else:
				print("Error: trying to apply(call) something that's not a function")
				assert False
		
		if isinstance(expr,Abs):
			#make sure the type of the bound var passes a type-check
			#with the current environment. what does "pass" really
			#mean here?
			type_check(expr.ch.type,env)
			
			#copy the set of type assumptions into a new set
			tmp_env = dict(env)
			
			#add a type assumption for the bound variable to the
			#new set
			tmp_env[expr.ch.var.varName] = expr.ch.type
			
			#type-check the body of the abstraction using the new
			#set of type assumptions
			expr_t = type_check(expr.ch.exp,tmp_env)
			
			#abstractions have Pi-types as their types
			#so we're expecting the result of running type_check on
			#expr.ch.exp to be able to potentially return a type expression
			#that depends on 'expr.ch.var' ?
			
			rt = PiType({'arg':expr.ch.var,'type':expr.ch.type,'ret':expr_t})
			
			#now that we've constructed the pi-type for our lambda abstraction,
			#we're going to type-check the pi-type itself and make sure it
			#passes. what does "pass" really mean here?
			type_check(rt,env)
			
			#return the pi-type if it passes the type-check
			return rt
		
		if isinstance(expr,PiType):
			#type-check-reduce the input type
			s = whnf(type_check(expr.ch.type,env))
			
			#copy the set of type assumptions into a new set
			tmp_env = dict(env)
			
			#add a type assumption for the bound variable to
			#the new set
			tmp_env[expr.ch.arg.varName] = expr.ch.type
			
			#type-check-reduce the body of the abstraction
			#using the new set of type assumptions
			t = whnf(type_check(expr.ch.ret,tmp_env))
			
			
			#both s and t should be either * or []
			#at least if they're expected to *maybe* be
			#in "allowedKinds".
			
			#check if the particular combination is
			#allowed by the cube-configuration:
			#if not, fail type-checking. this is how
			#we control what corner what of the cube
			#we're using
			if ( (s.__class__,t.__class__) not in allowedKinds):
				print ("Bad abstraction, AllowedKinds=", 
				[(x.__name__, y.__name__) for x,y in allowedKinds], ", argtype, bodytype = ", (s.__class__.__name__,t.__class__.__name__))
				assert False
			
			#the type of a pi-type is the type of it's body?
			#
			#why?
			return t
		
		
		#single 'axiom' of our type theory, star's type is box:
		# "* : []"
		#
		#why?
		if isinstance(expr,StarKind):
			return BoxKind({}) 
		
		#box has no type. if we end up having to type-inference
		#for a box, then fail. 
		#
		#why?
		if isinstance(expr,BoxKind):
			print("Error: found a box")
			assert False
	
	allowedKinds = [(StarKind, StarKind), (BoxKind, StarKind)]
	
	
	#The FreeVars function is still straight-forward
	#enough. What's less straight-forward to understand is
	#the mechanics of the language when the extra lambda
	#cube dependencies are added in.
	def FreeVars(expr, vars=None) -> set:
		if (vars == None): vars = set()
		
		#if the expression is a variable, add it
		#to the list of free variables. so what
		#happens to bound variables? they get removed
		#from the list in the abstraction case.
		if isinstance(expr,Var):
			vars.add(expr.ch.var.varName)
			return vars
		
		#the free variables of an application is
		#the union of the free variables in each
		#of its components (function and argument)
		if isinstance(expr,App):
			free_e1 = FreeVars(expr.ch.e1,vars)
			return free_e1.union(FreeVars(expr.ch.e2,vars))
		
		#we don't care whether the variables are occurring
		#in an expression or its type, we just care where
		#variables are occurring, cause when we get into
		#the full lambda cube dependencies, things can be
		#going everywhere
		
		#the free variables of a typed abstraction is
		#the union of the free variables in it's input-type
		#component with the free variables in it's body
		#component, with the bound variable removed
		if isinstance(expr,Abs):
			free_t = FreeVars(expr.ch.type,vars)
			free_e = FreeVars(expr.ch.exp,vars)
			free_e.remove(expr.ch.var.varName)
			return free_t.union(free_e)
		
		#the free variables of a pi-type is the union
		#of the free variables in it's input-type component
		#with the free variables in it's body component,
		#with the bound variable removed
		if isinstance(expr,PiType):
			free_t = FreeVars(expr.ch.type,vars)
			free_e = FreeVars(expr.ch.ret,vars)
			free_e.remove(expr.ch.arg.varName)
			return free_t.union(free_e)
		
		#the expressions "*" and "[]" don't contain
		#any variables, just return the current list of
		#free vars
		if type(expr) in [StarKind,BoxKind]:
			return vars
	
	
	
	#substitute "what" with "by" in "where"
	#he says his is is subst(what,where,by)
	#or                subst(v,   x,    e)
	#
	#but it's really   subst(what,by,where)
	def subst(where,what,by):
		#if the 'where' expression is the var that we're
		#substituting, then make the substitution, otherwise
		#just return 'where'.
		if isinstance(where,Var):
			if(where.varName == what.varName):
				return by
			else:
				return where
		
		#make the substitution into both the function and the argument
		#in an application
		if isinstance(where,App):
			return App({'e1':subst(where.ch.e1,what,by),'e2':subst(where.ch.e2,what,by)})
		
		
		
		if isinstance(where,Abs):
			#if the bound variable of the abstraction is the var
			#we're supposed to be substituting, then i guess we
			#say this new occurrence of a bound variable with the
			#same name shadows the substitution-variable in the
			#body expression. however, we still might be making the
			#substitution in the expression for the input-type of
			#the abstraction (i.e. dependent types & type operators)
			if(where.ch.var.varName == what.varName):
				return Abs({
					'var':where.ch.var.varName,
					'type':subst(where.ch.type,what,by),
					'exp':where.ch.exp
					})
			
			#else if the bound variable of the abstraction is in
			#the free variables of the 'by' expression, then 
			#replace the bound variable in the abstraction with a
			#fresh variable so that it won't interfere with the
			#free variables in 'by'. then substitute 'by' for 'what'
			#in both the input-type and the abstraction body
			elif (where.ch.var.varName in FreeVars(by)):
				z = genFreshVarName()
				t1 = subst(where.ch.exp,where.ch.var,z)
				return Abs({
					'var':z,
					'type':subst(where.ch.type,what,by),
					'exp':subst(t1,what,by)
					})
			
			#else we can just make the substitution directly since
			#there's no free-variable interference or scoping/shadowing
			#issues:
			else:
				return Abs({
					'var':where.ch.var,
					'type':subst(where.ch.type,what,by),
					'exp':subst(where.ch.exp,what,by)
					})
		
		#Pi's should work just like Abs
		if isinstance(where,PiType):
			if (where.ch.arg.varName == what.varName):
				return PiType({
					'arg':where.ch.arg,
					'type':subst(where.ch.type,what,by),
					'ret':where.ch.exp
					})
			
			elif (where.ch.arg.varName in FreeVars(by)):
				z = genFreshVarName()
				t1 = subst(where.ch.ret,where.ch.arg,z)
				return PiType({
					'arg':z,
					'type':subst(where.ch.type,what,by),
					'ret':subst(t1,what,by)
					})
			
			else:
				return PiType({
					'arg':where.ch.arg,
					'type':subst(where.ch.type,what,by),
					'ret':subst(where.ch.ret,what,by)
					})
		
		#* and [] both don't contain any vars so you're not gonna
		#substitute anything into them. return the expression as is.
		if isinstance(where,Kind):
			return where
	
	#Alpha equivalence: check if the two expressions are
	#equivalent under variable renaming.
	def alphaEq(expr1,expr2):
		if (type(expr1) != type(expr2)): return False
		
		#ok, so this looks like it's explicitly *not* checking
		#if it's equivalent under renaming, since it's checking
		#if the names are equal.
		
		#this is accounted for by the rest of the function
		#when we encounter lambdas, we transform the 2nd expression
		#so that it's bound variable matches that of the 1st
		
		#that being said, i noticed some people in the comments
		#were pointing out small mistakes here and there, so once
		#we have it all down we might be on our own in ensuring that
		#it's 100% correct (not just this function but the whole thing)
		
		#what happens if it just gets two variables as the argument
		#expressions? no renaming happens so we'd fail alphaEq
		#in untyped lambda calculus we can have vars outside of
		#abstractions
		if (type(expr1) == Var):
			return (expr1.varName == expr2.varName)
		
		#App is simple enough, just check if both the functions
		#are alpha equivalent and if both the arguments are
		#alpha equivalent
		if (type(expr1) == App):
			return (alphaEq(expr1.ch.e1,expr2.ch.e1) 
				and alphaEq(expr1.ch.e2,expr2.ch.e2)
				)
		
		#Two abstractions with different bound variables can
		#mean the same thing, i.e. they would be the same
		#under a suitable variable renaming.
		
		#check if the input types are alpha equivalent, then
		#replace the bound variable in the second abstraction 
		#with the bound variable from the first lambda abstraction
		#and see if their bodies are syntactically equal
		
		#the syntactic equality is enforced by recursing down to the 
		#Var case above
		if (type(expr1) == Abs):
			return (alphaEq(expr1.ch.type,expr2.ch.type)
				and alphaEq(
					expr1.ch.exp,
					subst(expr2.ch.exp,expr2.ch.var,expr1.ch.var)
					)
				)
		
		#dependent function types
		#\x:t.x->x. 
		#not sure how to construct a type using terms.
		#
		#check if the input types are equal
		#replace the bound variable in the second pi-type
		#with the bound variable from the first and check
		#if their bodies are alpha-equivalent.
		if (type(expr1) == PiType):
			return (alphaEq(expr1.ch.type,expr2.ch.type)
				and alphaEq(
					expr1.ch.ret,
					subst(expr2.ch.ret,expr2.ch.arg,expr1.ch.arg)
					)
				)
		#there's only one * and there's only one [], and we know
		#by this point that the type()'s must be equal, so if
		#one of the expressions is * or [], then they both are,
		#and they're the same
		if (type(expr1) == StarKind):
			return True
		if (type(expr1) == BoxKind):
			return True
	
	
	
	#reduce both expressions to normal form and then check if they are
	#alpha-equivalent
	def betaEq(expr1,expr2):
		return alphaEq(nf(expr1),nf(expr2))
	
	
	
	#no idea wth is going on with nf() and whnf() here.
	#return the normal form of the expression
	#aka normalize()
	#aka evaluate()
	#aka beta-reduce()
	#... people should stop making new names for this thing
	#def nf(expr):
	#	return nf_spine(expr,[])
	
	#nf :: Expr -> Expr
	#nf ee = spine ee []
	#where spine (App f a) as = spine f (a:as)
	#spine (Lam s t e) [] = Lam s (nf t) (nf e)
	#spine (Lam s _ e) (a:as) = spine (subst s a e) as
	#spine (Pi s k t) as = app (Pi s (nf k) (nf t)) as
	#spine f as = app f as
	#app f as = foldl App f (map nf as)
	
	#dehaskellified
	def nf(expr):
		if type(expr) in [Var,StarKind,BoxKind]:
			return expr
		
		if isinstance(expr,App):
			nf1 = nf(expr.ch.e1)
			if isinstance(nf1,Abs):
				return nf(subst(nf1.ch.exp,nf1.ch.var,expr.ch.e2))
			
			else:
				print("What are you trying to normalize here?")
				assert False
		
		if isinstance(expr,Abs):
			return Abs({'var':expr.ch.var,'type':nf(expr.ch.type),'exp':nf(expr.ch.exp)})
		
		if isinstance(expr,PiType):
			return PiType({'arg':expr.ch.arg, 'type':nf(expr.ch.type),'ret':nf(expr.ch.ret)})
	
	
	
	
	
	
	#return the "weak head normal form" of the expression
	
	#whnf :: Expr -> Expr
	#whnf ee = spine ee []
	#where spine (App f a) as = spine f (a:as)
	#spine (Lam s e) (a:as) = spine (subst s a e) as
	#spine f as = foldl App f as
	
	def whnf(expr):
		#variables, abstractions, and pi-types are already in weak-head normal form
		#so just return them
		if type(expr) in [Var,Abs,PiType,StarKind,BoxKind]:
			return expr
		
		#if it's an application then we check whether there's an
		#application or an abstraction in the function position
		#(it shouldn't be anything else)
		if isinstance(expr,App):
			#if it's an abstraction in function position, then
			#we apply it to the argument. 
			#need to make sure the value we get as a result of this
			#is also in weak-head normal form.
			#i don't think he does this in "simpler, easier"
			if isinstance(expr.ch.e1,Abs):
				return whnf(subst(expr.ch.e1.ch.exp,expr.ch.var,expr.ch.e2))
			
			#if it's an application in function position, then
			#we whnf() that application and return a new application
			#that has this new expression as e1, but the same argument
			#for e2
			if isinstance(expr.ch.e1,App):
				return App({'e1':whnf(expr.ch.e1),'e2':expr.ch.e2})
			
			else:
				print("What are you trying to normalize here?")
				assert False
		
		else:
			print("What are you trying to normalize here?")
			assert False



















	ParExp.unparen = lambda s: s.ch.exp.unparen()

	def eval(e):
		x = e.copy().unparen()
		#print (x.tostr())
		n = nf(x)
		assert n
		return n.copy()

	for x in [ParExp, App, Abs, Var, PiType, StarKind, BoxKind]: x._eval = eval
	for x in [ParExp, App, Abs, Var, PiType, StarKind, BoxKind]: x.type_check = type_check






	
	"""
        class IntType(Syntaxed):
                help = ["integer type"]
        build_in(SyntaxedNodecl(IntType,
                [TextTag("int")],
                {}), None, lc2)
        class BoolType(Syntaxed):
                help = ["bool type"]
        build_in(SyntaxedNodecl(BoolType,
                [TextTag("bool")],
                {}), None, lc2)

	"""
"""

Expr 		:=	Expr1 | "(" Expr ")"
Expr1		:=	Var | Abs | App
Var		:= 	Char Name # Identifier
Abs		:=	"|" Var "." Expr
App		:=	Expr " " Expr
Name		:=	<endword> | Char Name
Char		:=	"a" | "b" | "c" | ... | 
			"A" | "B" | ... |
			"1" | "2" | ... | 
			"_" ...

//possibly
NamedExpr	:=	Name ":=" Expr

so i guess the question wrt syntax is how do you tell a named expression
from a var or do you, if not, 
i'm thinking you can treat everything that's syntactically the same as
a var as "potentially a named expression"
but, it gets kinda syntactically messy when you can have things like

myFunc := ...

myOtherFunc := \\myFunc.myFunc
		^ for example, myFunc in this expression would be
		taken as a var, even though myFunc is defined before it
		
myThirdFunc := \\x.(myFunc x)
		  ^ the name doesn't correspond to a bound var, so
		  treat it as the func
		  
it's perhaps slightly contrived, but it is unambiguous at least,
and rather simple

i don't think  we should make implementing anything contrived be
a priority tho. to me, the main critical piece is to be able to
make a full spectrum of logic systems, from the utlc up through
fully dependently typed lambda calc, i.e. MLTT or even HoTT

secondary for me is sugaring to interface to these logics
(at least until we've implemented the different logics, then
this one will become primary for me)

so..we need a table right? like the thunks table
yea, at the very least we need a table of expression definitions
so that the evaluator can call them up when needed
if the expressions in this table can have their definitions updated
when they get evaluated, and newly-found expressions can be added
to the table, then we basically have haskell's table of thunks
and we basically have lazy evaluation
newly-found? so, once the expression starts evaluating then it
can generate 'new' expressions over the course of its evaluation
umm
you mean it can evaluate to a new expression to be put in its place or
something else? both, the something else would be evaluating to an
expression that contains multiple instances of the same sub-expression,
where these sub-expressions "haven't been seen before", so they'd
essentially get a new entry in the table

i'm not aware to what extents haskell does the second part
ahh so this is an optimization only? i mean the repeated expression "elimination"
yep that's basically all lazy evaluation is hmm

according to wiki "is an evaluation strategy which delays the evaluation
of an expression until its value is needed (non-strict evaluation), 
and which also avoids repeated evaluations (sharing)."

so, it's basically the evaluation strategy we have hooked up already,
combined with this repeated-expressions optimization

ok yea i see kinda...
im ready to crash
sounds good, anything else would be too much to get into tonight anyway
yeah half past two, i should
i guess tomorrow before i wake up give some thought to what you wanna
implement next, i'm gonna keep focusing on the plans for the simply
typed lambda in the meantime tho
sounds good
getting an idea of proper typing does sound more important
for us i think so
especially cause as we proceed into the dependent typing this
intersects back with tau, so, killing multiple birds and all that
alright
catch you tomorrow later


does haskell have different naming schemes?
well, haskell has the whole typing thing so they get a lot more
info about what the expression is supposed to be

and then to actually evaluate the expression they use the
pattern matching thing, and i think that doing these things
they basically make it completely unambiguous

so..what do you suggest?

one potential unambiguous naming scheme would be to treat
names that have a corresponding expression as expressions unless
that name is a bound var

yea we could do that, couple things to figure out with it,
first thing is getting a complete syntax for it

would this be used like
it would be like
"def Name:
	Expr"
<some expression using Name>
more definitions
more expressions


or just like


definition 1
definition 2
oneandonlyexpression

probably more like

definition 1
definition 2
def Main:	<--but yea this is essentially our
		"one and only expr"
	...

if you add more expressions to evaluate that's just
basically running multiple programs in sequence
(but perhaps reusing definitions between them)
well, at least that's a "typical interpretation" of the
situation

could also interpret it as running a sequence of commands, all
within the same program

but... *shrug*

i think the more critical point is that by introducing named
expressions we might actually be making it something slightly
different than 'proper' lambda calculus

notice that a lambda expression cannot be recursive
the language doesn't even have the capacity to express a recursion
recursive behavior can be recovered through use of clever arguments
like
(\\a.(a a)) (\\a.(a a)) --eval-to--> (\\a.(a a)) (\\a.(a a))

but this is a different mechanism than

def myFunc := \\a.(myFunc a)

ok, so i understand it as a whole new macro language
that's probably the most appropriate interpretation

*scratches head* wrt anything in particular?
the motivation i guess, behind lambda calc?
behind the naming thing
well, makes it more like a real prog-lang,
it's something i just thought to add before we really
got into it and i saw that these kinds of recursions aren't
actually part of the lambda calc itself

so, can we perhaps look at haskell and define the semantics of this 
new language? the new language being this utlc + the naming thing?
kinda just the naming thing separately ah
yea, could look at just about any lang for this
haskell is like utlc + naming thing + simple typing + sugar

this naming thing actually has to be mada a part of the evaluator right?
yea, if we tried to macro expand with essentially recursively defined
macros, then... yea
haskell doesn't really have a problem with that because they're already
storing a bunch of thunks for their lazy evaluation
hmm not sure what that means but i guess ill see later

i'm not 100% how the details work, but haskell basically stores an
index to references to partially evaluated expressions, called thunks, 
so if the same sub-expression is used multiple times in the 
super-expression, then if you evaluate the first instance of the
sub-expression, you've evaluated all instances, because the other
instances are just referencing this thunk that's now been evaluated

so, they're already handling all this stuff at the evaluator level
anyway just to implement lazy evaluation
ah





//not all applications are function applications, cf. "y y"
but the var could evaluate to a function
unless we've reached normal form, i.e. nothing left to evaluate
so is this a syntax for normal form or nonnormal form?
could be either one. 

|x.(x x) y  --reduce--> y y, and nothing left to evaluate so this is in normal form
    ^ also occurs in the original expression here

|y.(|x.(x x) y) |w.w --reduce -->
|y.(y y) |w.w  --reduce -->
    ^ here it occurs, but it's not in normal form

lambda calculus is quite hard to follow
i agree. it's mainly only of theoretical interest until you get
some relatively sophisticated syntax for it
i would probably start without the redex/nonredex distinction so we can meaningufully express even nonnormal programs, hrm, i don't think we need the redex/nonredex distinction for the syntax
|w.w |w.w --reduce-->
|w.w



1) Parse query according to BNF above

2) If it parses, then normalize the expression


//Need to choose reduction strategy:
//There are several options:
/* * Full beta reduction: non-normalizing
	Any reducible expression can be reduced at any time.
   	This is essentially the lack of any particular reduction
	strategy, or equivalently the union of all reduction strategies.


   * Applicative order: non-normalizing
	Rightmost, innermost reducible expression is always reduced first.
	This means a function's arguments are always reduced before the
	function itself.

   * Normal order:
	The leftmost, outermost reducible expression is always reduced first.

   * Call by name:
	Same as normal order except no reductions are performed inside abstractions.
	For example: |x.((|x.x) x) would be considered to be in normal form, even
	though it contains the reducible expression ((|x.x) x). Since this redex
	occurs inside an abstraction, it is not to be reduced.

   * Call by value:
	?

   * Call by need:
	aka "lazy evaluation"
	Function applications that would duplicate terms will name the argument
	instead, which is then reduced only "when it is needed", and which will
	represent all duplicated versions of itself. i.e. if you reduce one of
	the duplicates, then they are all reduced, as they will just be names
	referring to an expression that is now reduced.

	This is the one to use, but the tradeoff is it's more complex to
	implement.	

*/		

//aka evaluate
//Normal order:
Normalize (Expr e) :=
	if (e is a Var x)
		return e
	if (e is an Abs x e1)
		return (Abs x normalize(e1))
	if (e is an App e1 e2)
		if(e1 is an Abs x e3)
			//one-step evaluation:
			return subst(e3,x,e2)
		ah so we should pick one here	
			//full evaluation:
			return normalize(subst(e3,x,e2))
		if(e1 is an App e3 e4)
			
		else return e



//applicative order:
Normalize (Expr e) :=
	if (e is a Var x)
		return e
	if (e is an Abs x e1)
		return e
	if (e is an App e1 e2)
		if(e1 is an Abs x e3)
			//first check if the rightmost expression is reducible
			if(isReducible(e2))
				//one-step evaluation
				return (App e1 normalize(e2))

				//full evaluation
				return normalize((App e1 normalize(e2)))

			//if not, then check if the innermost expression is
			//reducible
			if(isReducible(e3))
				//one-step evaluation
				return (App (Abs x normalize(e3)) e2)

				//full evaluation
				return normalize((App (Abs x normalize(e3)) e2))

			//neither the rightmost nor innermost expressions are
			//reducible
			return subst(e3,x,e2)
		else return e


//call by name
Normalize (Expr e) :=
	if (e is a Var x)
		return e
	//unlike normal order we don't normalize inside abstractions
	if (e is an Abs x e1)
		return e
	if (e is an App e1 e2)
		if (e1 is an Abs x e3)
			//one-step evaluation:
                        return subst(e3,x,e2)

                        //full evaluation:
                        return normalize(subst(e3,x,e2))
                else return e


//call by value
evaluate arguments to functions first before substituting them into
the function

this actually not one single evaluation strategy but is the family of
evaluation strategies where the arguments are normalized before substituting
them into the function. 

here's one example that does this but follows the normal order evaluation
strategy otherwise


Normalize (Expr e) :=
	if (e is a Var x)
		return e
	if (e is an Abs x e1)
		return e
	if (e is an App e1 e2)
		if(isReducible(e2))
			//one step evaluation
			return (App e1 normalize(e2))

			//full evaluation
			return normalize(App e1 normalize(e2))
		if (e1 is an Abs x e3)
			//one step evaluation
			return subst(e3,x,e2)
		
			//full evaluation
			return normalize(subst(e3,x,e2))
		else return e



//call by need (aka lazy evaluation)
need some mechanism for storing and retrieving the thunks
expressions look different internally: composed of references
to thunks




//call by reference

//call by sharing

//call by copy-restore

//call by future

//optimistic evaluation

//partial evaluation




An expression is reducible if contains anything that can be reduced.
The only things that can be reduced are of the form (App (Abs x e1) e2)

//The expression contains a "top-level" reducible expression
//meaning the reducible expression does not occur inside the body
//of an abstraction.
isReducible(Expr e) :=
	if(e is a Var x) return false
	if(e is a Abs x e1) return false
	if(e is a App e1 e2)
		if(e1 is a Abs x e3) return true
		if(e1 is a Var x) return false
		if(isReducible(e1)) return true
		if(isReducible(e2)) return true
		else return false
	
//The expression contains a reducible expression anywhere,
//possibly in the body of an abstraction.
isReducible2(Expr e) :=
	if(e is a Var x) return false
	if(e is a Abs x e1) return isReducible2(e1)
	if(e is a App e1 e2)
		if(e1 is a Abs x e3) return true
		if(e1 is a Var x) return false
		if(isReducible2(e1)) return true
		if(isReducible2(e2)) return true
		else return false


//capture-avoiding substitution:
subst(Expr e, Var x, Expr r) :=
	replace all occurrences of x in e with r, potentially
	changing variable names to avoid variable capture.

	capture-avoidance:
	don't let free variables become bound
	
/*
	//This is the var we're substituting, so make
	//the substitution
	(Var x)[x := r]		= r
	
	//This is a different var than the one we're substituting,
	//don't substitute anything
	(Var y)[x := r]		= y

	//Substitute into each component of an application:
	(App t s)[x := r]	= (t[x:=r])(s[x:=r])
				= App subst(t,x,r) subst(s,x,r)

	//if the substitution-variable is the same as the bound-variable
	//of an abstraction, then don't substitute, even in the expression t.
	//why?
	//answer 1: just because
	//answer 2: ??
	(Abs x t)[x := r]	= (Abs x t).

	
	//naive version:
	//if the substitution-variable is *not* the same as the bound-variable
	//of an abstraction, then substitute [x := r] in t
	//there is nothing to avoid variable capture here.
	(Abs y t)[x := r]	= (Abs y subst(t,x,r))


	//capture-avoiding version:
	//if the substitution-variable is *not* the same as the bound-variable
	//of an abstraction, then if y is not in the FreeVars of r, then
	//apply the substitution in the body of the abstraction.
	//if y *is* in the FreeVars of r, then we'll rename y to a
	//fresh variable name, z, and substitute z for y across the
	//entire abstraction.
	//then we will proceed with our usual substitution of r for x,
	//as defined in the naive version.
	(Abs y t)[x := r]	= 
		if(y not in FreeVars(r)) -> (Abs y subst(t,x,r))
		else
			z = genFreshVarName()
			t' = subst(t,y,z)
			t'' = subst(t',x,r)
			return (Abs z t'')


*/


FreeVars(Expr e, List<Var> * ret) :=
	if (e is a Var x) 
		ret = set_union(ret,{x})
		return
	if (e is a Abs x e1)
		free_e := FreeVars(e1)
		remove x from free_e
		ret = set_union(ret,free_e)
		return
	if (e is a App e1 e2)
		free_e1 := FreeVars(e1)
		free_e2 := FreeVars(e2)
		ret = set_union(ret,free_e1,free_e2)
		return



//eta-conversion

f == |x.(f x)

//not really necessary. not sure where this would even come up in normal
//programming with lambdas. for theorem proving otoh, there's reason to use it

















# cool i guess that's everything from the bnf then
# yeah next i have to finish the parser
# cool so how does what we have here fit into that
#well, the gui is set up so that when you go into lc1-test, it
#collects the grammar from the nodes in its scope

the above module now looks like this in the gui:
[lc1]:<module[]from[]:
<<->[ 
    <syntactic category:[exp]>
    <var:
        a variable
        example: <{}>>
    <parexp:
        a parenthesized expression
        example: <({})>>
    <<*parexp>works as<*exp>>
    <abs:
        abstraction, a lambda
        example: <|
        
        
        {}.{}>>
    <app:
        function application, a call
        example: <{} {}>>
    ]>end.>

the "example:"'s dont work very well yet
it doesnt even display the syntaxes, too










this is the grammar of the particular node type
		[TextTag("("), ChildTag("exp"), TextTag(")")],
it has to go over this list
ah it goes over the list to generate a grammar for marpa
yeah to call marpa .symbol and .rule functions








-       #i need to think a bit if we need to do anything different for our base types
-       #but, not sure, maybe we should just start working on the logic and it might
-       #become more clear
-       #in tau HMC doesn't even want to have these types explicitly,
-       #apparently everything can be made with pi's and sigmas
-       #the article also doesn't give any mention to these so... need to think it over a bit
-       #i would guess they wont be a problem but no idea
-       #i'm gonna assume that if the article doesn't use them then they're unnecessary
-       #cause he does use base types in the simply typed lambda, but then they seem to
-       #mysteriously disappear in the lambda cube section, and his example expressions
-       #don't make any use of anything except the syntax we've already got laid out above
-       #mm, then lets get it working without i guess




"""
