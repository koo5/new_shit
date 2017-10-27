# -*- coding: utf-8 -*-

"""

this file defines the AST classes of the language and everything around it.
the philosophy of this codebase is "constant surprise". it keeps you alert.
"kids" and "children" mean the same.
sometimes i use "s" instead of "self".
"ch" is children of syntaxed.
good luck.

"""


import sys
class __LINE__(object):

    def __repr__(self):
        try:
            raise Exception
        except:
            return str(sys.exc_info()[2].tb_frame.f_back.f_lineno)

__LINE__ = __LINE__()


lang = cs = en = None
def go_cs():
	lang = "cs"
	cs = True
	en = False
def go_en():
	lang = "en"
	en = True
	cs = False
go_cs()
from localization import localized

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

from marpa_cffi.valuator_actions import *

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
	elif isinstance(d, (CompoundNodeDef, Union)):
		return d
	elif is_decl(d) or d == None or isinstance(d, SyntacticCategory):
		return d
	else:
		raise Exception("i dont knwo how to deref "+repr(d)+", it should be a type or something")

def deref_def(d):
	if isinstance(d, Ref):
		return deref_def(d.target)
	elif isinstance(d, Definition):
		return d
	elif isinstance(d, (CompoundNodeDef, Union)):
		return d
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

#where does .module.inst_fresh() come from? #the nodecl
#is this a python-ism? nope, its a lemon-nodes-ism
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
	"""this is the class of "ch" of Syntaxed nodes"""
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
	logging.getLogger("serialization").debug("deserializing node with decl %s"%repr(decl))
	if decl == 'Parser': # ok, some nodes are special, we dont have a nodecl for Parser
		return Parser.deserialize(data, parent)
	elif decl == 'defun': # i dont save the exact class of functions definitions, makes it easier to change functions from BuiltinPythonFunctionDecl to FunctionDefinition, for example
		return FunctionDefinitionBase.deserialize(data, parent)
	#if decl == 'varref':
	#	return VarRef.deserialize(data, parent)
	elif isinstance(decl, unicode): # we will look for a nodecl node with this name
		decl = find_decl(decl, parent.nodecls)
		if decl:
			logging.getLogger("serialization").debug("deserializing item with decl %s thru class %s"%(decl, decl.instance_class))
			return decl.instance_class.deserialize(data, parent)
		else:
			logging.getLogger("serialization").debug("nodecl node not found")
			raise DeserializationException ("cto takoj " + repr(decl))
	elif isinstance(decl, dict): # the node comes with a decl as, basically, its child
		decl = deserialize(decl, parent)



		try:
			logging.getLogger("serialization").debug("got %s, lets deref_decl it..."%decl)
			ddd = deref_decl(decl)
			logging.getLogger("serialization").debug("ok thats %s" % ddd)
			return ddd.instance_class.deserialize(data, parent)
		except DeserializationException as e:
			#logging.getLogger("serialization").debug(e)
			print (e)
			#raise
			return failed_deser(data, parent)


	else:
		raise DeserializationException ("cto takoj " + repr(decl))

def failed_deser(data, parent):
	"""create a Serialized node that holds the data that failed to deserialize"""
	assert parent
	r = Serialized.fresh()
	r.parent = parent
	if 'last_rendering' in data:
		p = Parser()
		r.ch.last_rendering = p
		p.items.append(Text(data['last_rendering']))
	r.ch.serialization = to_lemon(data)
	r.fix_parents()
	return r


def find_decl(name, decls):
	"""find decl by name"""
	assert isinstance(name, unicode)
	for i in decls:
		if name == i.name:
			logging.getLogger("serialization").debug("found:%s",name)
			return i
	raise DeserializationException ("%s not found in %s"% (repr(name), repr(decls)))


def resolve(data, parent):
	assert parent
	assert(data['resolve'])
	logging.getLogger("serialization").debug("resolving %s", data)
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
				logging.getLogger("serialization").debug('dd1:%s, dd2:%s'%(dd1,dd2))
				if dd1 == dd2:
					logging.getLogger("serialization").debug("in scope:%s",i)
					if i.name == name:
						return i
			raise DeserializationException("node not found: %s ,decl: %s"%(data,decl))

	elif 'class' in data:
		sought_name = data['name']
		sought_class_name = data['class']
		logging.getLogger("serialization").debug("looking for name:%s, class:%s", sought_name, sought_class_name)
		for i in scope:
			class_name = i.__class__.__name__.lower()

			if class_name == sought_class_name:
				name = i.name
				logging.getLogger("serialization").debug("class:%s, name:%s",class_name, name)
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
		r["last_rendering"] = s.tostr()
		r.update(s._serialize())
		print("saving...", json.dumps(r, indent = 4, sort_keys=True))
		return r

	def serialize_decl(s):
		if s.decl:
			logging.getLogger("serialization").debug("serializing decl %s of %s"%(s.decl, s))
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

		r.view_mode = 2
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
		logging.getLogger("serialization").debug('vardecl decl:%s', decl)
		for i in parent.vardecls_in_scope:
			logging.getLogger("serialization").debug('i in parent.vardecls_in_scope:%s',i)
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
		r = cls()
		r.parent = parent
		logging.getLogger("serialization").debug("deserializing Parser "+str(data))
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
		for i in funcs:
			logging.getLogger("serialization").debug("function considered:%s"%i)
		raise DeserializationException("function not found by sig:%s" % sig)#json.dumps(sig, indent = 4, sort_keys=True))

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

	def clipboard_cut(s):
		s.clipboard_copy()
		s.parent.delete_child(s)

	def clipboard_copy(s):
		print ("copy")
		s.root["clipboard"].ch.statements.add(s.copy())

	def symbol(s, m):
		if not s in m.node_symbols:
			logging.getLogger("marpa").debug(("gimme symbol for", s))
			s.register_symbol(m)
		if s in m.node_symbols:
			return m.node_symbols[s]

	def register_symbol(s, m):
		return register_symbol(s, m)

	@classmethod
	def register_class_symbol(cls, m):
		return register_class_symbol(cls, m)

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
		return scope_after_hiding_and_unhiding(s)

	def full_scope(s):
		return what_in_my_module_do_i_see(s) + what_module_sees(s.module)


	@property
	def nodecls(s):
		return [i for i in s.scope() if isinstance(i, (NodeclBase, EnumType))]

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
				yield [TextTag(str(len(v.items))), TextTag(localized(" values:")), ElementTag(v)]
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




class CompoundNode(Node):
	def __init__(s, decl):
		super().__init__()
		assert isinstance(decl, CompoundNodeDef)
		s.decl = decl
		s.create_kids()
		s.fix_parents()

	@classmethod
	def deserialize(cls, data, parent):
		assert parent
		placeholder = Text("placeholder")
		placeholder.parent = parent
		decl = deserialize(data['decl'], placeholder)
		r = cls(decl)
		r.parent = parent
		for k,v in iteritems(data['children']):
			r.ch[k] = deserialize(v, r)
		r.fix_parents()
		return r

	def _serialize(s):
		return odict(
			children = s.serialize_children()
		)

	def serialize_children(s):
		r = {}
		for k, v in iteritems(s.ch._dict):
			r[k] = v.serialize()
		return r

	def fix_parents(s):
		s._fix_parents(list(s.ch._dict.values()))

	@property
	def syntax(s):
		return deref_decl(s.decl).ch.syntax.parsed.items

	def create_kids(s):
		s.ch = Dotdict()
		for i in s.syntax:
			i = i.parsed
			if isinstance(i, TypedParameter):
				p = i.type.parsed
				if not isinstance(p, Bananas):
					ch = Parser()
				else:
					ch = Text("bad decl")
				s.ch[i.ch.name.parsed.pyval] = ch
		s.fix_parents()

	def render(s):
		for i in s.syntax:
			i = i.parsed
			if isinstance(i, Text):
				yield i.pyval
			elif isinstance(i, TypedParameter):
				yield ElementTag(s.ch._dict[i.ch.name.parsed.pyval])

	def child_type(s, ch):
		for name,v in iteritems(s.ch._dict):
			if v == ch:
				for i in s.syntax:
					i = i.parsed
					if isinstance(i, TypedParameter):
						if i.ch.name.parsed.pyval == name:
							return i.ch.type.parsed
		assert False

	def _flatten(s):
		assert(isinstance(v, Node) for v in itervalues(s.ch._dict))
		return [s] + [v.flatten() for v in itervalues(s.ch._dict)]


class Syntax:
	def __init__(s, descriptive_tags, rendering_tags):
		s.descriptive_tags = descriptive_tags
		s.rendering_tags = rendering_tags


class Syntaxed(SyntaxedPersistenceStuff, Node):
	"""
	Syntaxed has some named children, kept in s.ch.
	their types are in s.slots.
	syntax is a list of Tags, and it can contain ChildTag
	"""
	brackets = ("<", ">")
	brackets = (" ", " ")
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
	def rule_for_syntax(cls, m, cls_sym, syntax, ddecl):
		syms = []
		
		
		for i in syntax.rendering_tags:
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
					x = B.expression.symbol(m)
				else:
					x = deref_decl(child_type).symbol(m)
				if not x:
					warn("no type:" + str(i))
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
		logging.getLogger("valuation").debug('Syntaxed from_parse(marpa value: %s   ,Syntax object: %s',p,sy)

		r = cls.fresh()
		#info((p, cls, sy))

		s2 = []
		for i in sy.rendering_tags:
			if type(i) == unicode:
				for ch in i:
					s2.append(ch)
			else:
				s2.append(i)


		#print(sy)
		#print(s2)

		si = 0#syntax_item_index

		for i in p:
			if type(i) == unicode:
				assert type(s2[si] == unicode)
			else:
				assert isinstance(i, Element),    i
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
		return s.syntaxes[s.syntax_index].rendering_tags

	@property
	def syntaxes(s):
		return s.ddecl.instance_syntaxes

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
				a = Parser()
			assert(isinstance(a, Node))
			kids[k] = a
		return kids

	@property
	def name(s):
		"""override if this doesnt work for your subclass"""
		return s.ch.name.pyval

	@property
	def slots(s):
		return s.ddecl.instance_slots

	def child_type(s, ch):
		for k,v in iteritems(s.slots):
			if s.ch[k] == ch:
				return v
		assert False

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.ch)+"')"

	def eq_by_value(a, b):
		assert len(a.ch._dict) == len(b.ch._dict) #are you looking for eq_by_value_and_decl?
		for k,v in iteritems(a.ch._dict):
			if not b.ch[k].eq_by_value_and_python_class(v):
				return False
		return True

	def copy(s):
		decl = s.decl.copy()
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

	def copy(s):
		r = s.__class__.fresh()
		r.decl = s.decl.copy()
		for k,v in iteritems(s.items):
			r.ch[k.copy()] = v.copy()
		r.fix_parents()
		return r

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
		s.parser_class = Parser

	def copy(s):
		r = s.__class__.fresh()
		r.decl = s.decl.copy()
		for v in s.items:
			r.items.append(v.copy())
		r.fix_parents()
		return r

	@classmethod
	def from_parse(cls, x):
		logging.getLogger("valuation").debug('List from_parse: x=%s',x)
		if (len(x) == 4):
			del(x[1])
		assert x[0] in '[{'
		assert x[2] in ']}'
		if x[1] == 'nulled': x[1] = []
		assert type(x[1]) == list
		r = cls()
		r.items = x[1][::2]
		r.view_mode = r.vm_oneline
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
		p = s.parser_class()
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

	def add_below(s, x, y):
		i = s.items.index(x) + 1
		s.items.insert(i, y)
		y.parent = s

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

	def by_name(s, n):
		for i in s.items:
			i = i.parsed
			if isinstance(i, Syntaxed):
				if 'ch' in i.__dict__.keys():
					if 'name' in i.ch._dict:
						if i.name == n:
							return i
		assert False


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

def banana(text="error text"):
	return Text(text)#
	r = CompoundNode(s.root.essentials.banana)
	r.ch.info = Text(text)
	return r

class Bananas(Node):
	"""https://www.youtube.com/watch?v=EAmChFTLP4w&feature=youtu.be&t=2m19s"""
	help=["parsing failure. your code is bananas."]
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

	def _eval(s):
		return Number(s.pyval)

	@staticmethod
	def match(text):
		if text.isdigit():
			return True
			

class Text(WidgetedValue):
	easily_instantiable = True
	brackets = ('"', '"')
	def __init__(s, value="", debug_note=""):
		super(Text, s).__init__()
		s.widget = widgets.Text(s, value)
		s.brackets_color = colors.text_brackets
		s.debug_note = debug_note

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
	def from_parse(cls, args):
		return cls(''.join(args))


class RestrictedIdentifier(WidgetedValue):
	def __init__(s, value=""):
		super().__init__()
		s.widget = widgets.Text(s, value)

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
		s.essentials = Dotdict()

	def render(s):
		#there has to be some default color for everything, the rendering routine looks for it..
		return [ColorTag(colors.fg)] + s.render_items() + [EndTag()]

	def delete_child(s, child):
		log("I'm sorry Dave, I'm afraid I can't do that.")

	def delete_self(s):
		log("I'm sorry Dave, I'm afraid I can't do that ")

	#def okay(s):
	#	recursively check parents?



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

		for i in s.flatten():
			if isinstance(i, Serialized):
				print("warning: saving Serialized:%s"%i)
		ss = s.serialize()

		import json
		out = json.dumps(ss, indent = 4, sort_keys=True)
		with open(s.file_name, "w") as f:
			f.write(out)
			f.close()
		#log(out)
		log("saved to "+s.file_name)
		#except Exception as e:
		#	log(e)
		#	raise e

	def scope(s):
		return what_module_sees(s)

class BuiltinModule(Module):
	_name = "some builtin module"
	@property
	def name(s):
		return s._name
class LikiModule(Module):
	pass
class ModuleThatDoesntSeeAnythingExceptUnhide(Module):
	def scope(s):
		return [B.unhidenode, B.statement, B.text, B.anything, B.expression]
	def full_scope(s):
		return what_module_sees(s)

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
	def from_parse(cls, x):
		logging.getLogger("valuation").debug('Ref from_parse:'+str(x))
		return cls(x)

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

	"""
	@property
	def name(s):
		return s.names[lang]

	@property
	def names(s):
		return {'en': s.instance_class.__name__.lower(),
		'cs' : localize(s.names['en'])}
	"""
	def instantiate(s, kids):
		return s.instance_class(kids)

	def inst_fresh(s, decl=None):
		""" fresh creates default children"""
		return s.instance_class.fresh(decl)

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


class ExpNodecl(NodeclBase):
	def __init__(s):
		super(ExpNodecl, s).__init__(Exp)

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

class SyntaxedNodecl(NodeclBase):
	"""
	A Nodecl for a class derived from Syntaxed.
	instance_slots holds types of children, not Ref'ed.
	 children themselves are either Refs (pointing to other nodes),
	 or owned nodes (their .parent points to us)
	"""
	def __init__(s, instance_class, instance_syntaxes, instance_slots):
		super(SyntaxedNodecl , s).__init__(instance_class)
		s.example = None
		s.instance_slots = dict([(k, B[i] if isinstance(i, unicode) else i) for k,i in iteritems(instance_slots)])
		if isinstance(instance_syntaxes[0], list):
			s._own_instance_syntaxes = [s.to_syntax(i) for i in instance_syntaxes]
		else:
			s._own_instance_syntaxes = [s.to_syntax(instance_syntaxes)]
		s.clear_syntaxes()

	def to_syntax(s, rendering_tags):
		return Syntax(["en"], rendering_tags)

	@property
	def instance_syntaxes(s):
		return s._own_instance_syntaxes + s._additional_syntaxes

	def clear_syntaxes(s):
		s._additional_syntaxes = []

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
		s.decl = Ref(decl)
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
		text = deref_decl(s.decl).ch.options[s.value].parsed
		if isinstance(text, Text):
			return text.pyval
		return "errrr"

	def copy(s):
		return s.eval()

	def _eval(s):
		return EnumVal(s.decl, s.value)

	@classmethod
	def deserialize(cls, data, parent):
		assert parent
		placeholder = Text("placeholder")
		placeholder.parent = parent
		r = cls(deserialize(data['decl'], placeholder), data["value"])
		r.parent = parent
		return r

	def _serialize(s):
		return odict(
			value = s.value
		)



class EnumType(ParametricTypeBase):
	"""works as a type but doesnt descend from Nodecl. Im just trying stuff..."""
	def __init__(s, children):
		s.instance_class = EnumVal
		super(EnumType, s).__init__(children)
	def works_as(s, type):
		if isinstance(type, Ref):
			type = type.target
		if s == type: return True
	def inst_fresh(s):
		return EnumVal(s, 0)

	@property
	def name(s):
		return s.ch.name.pyval

#i *could* add register_class_s








class SyntacticCategory(Syntaxed):
	help=['this is a syntactical category(?) of nodes, used for "statement" and "expression"']

	def __init__(s, children):
		super(SyntacticCategory, s).__init__(children)

class WorksAs(Syntaxed):
	help=["declares a subtype relation between two existing types"]
	def __init__(s, children):
		super(WorksAs, s).__init__(children)

	@property
	def name(s):
		return object.__repr__(s)

	@classmethod
	def b(cls, sub, sup):
		"""building-in helper"""
		if isinstance(sub, unicode):
			sub = B[sub.replace(' ', '_')]
		if isinstance(sup, unicode):
			sup = B[sup.replace(' ', '_')]
		return cls({'sub': Ref(sub), 'sup': Ref(sup)})

	def is_relevant_for(s, scope):
		sub = s.ch.sub.parsed
		sup = s.ch.sup.parsed
		aa = deref_def(sub)
		bb = deref_def(sup)
		a = aa in scope
		b = bb in scope
		logging.getLogger("scope").debug("%s is_relevant_for scope? %s %s (%s, %s)", s.tostr(), a, b, aa,bb)
		return a and b

class BindsTighterThan(Syntaxed):
	help = ["has higher precedence, goes lower in the parse tree"]


class Definition(Syntaxed):
	"""should have type functionality (work as a type)*?*"""
	help=['used just for types, currently.']
	def __init__(s, children):
		super(Definition, s).__init__(children)

	def inst_fresh(s):
		return s.ch.type.inst_fresh(s)

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
			return banana('itemvar isnt UntypedVar')
		items = s.ch.items.eval()
		if not isinstance(items, List):
			return banana('items isnt List')
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
			return banana("%s is of type %s, i cant branch with that" % (c, c.decl))
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
			return banana("parent is not Statements")
		above = parent.above(child)
		if not len(above):
			return banana("no nodes above me, much less an If")
		a = above[-1].parsed
		if not isinstance(a, If):
			return banana("whats above me is not an If and that makes me sad")
		c = a.ch.condition
		if not 'value' in c.runtime._dict:
			return banana("the node above me wasnt evaluated, how am i to know if i should run?")
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
	def __init__(s):
		super(ParserBase, s).__init__()
		s.items = NotifyingList()
		s.decl = None
		s.on_edit = Signal()
		s.brackets_color = colors.compiler_brackets
		s.brackets = (' ', ' ')

	def clipboard_paste(s):
		print ("paste")
		s.add(s.root["clipboard"].ch.statements[-1].copy())

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
	_parsed = None
	_type = None
	def __init__(s):
		super(Parser, s).__init__()

	@property
	def parsed_symbol(s):
		return s.type.symbol

	@property
	def type(s):
		if s._type:
			return s._type
		p = s.parent
		if isinstance(p, Parser):
			return p.type
		elif isinstance(p, (Syntaxed, FunctionCall, CompoundNode)):
			return p.child_type(s)
		elif isinstance(p, (List, Dict)):
			return p.item_type
		elif isinstance(p, Serialized):
			return p.item_type

		else: assert False,    p

	def copy(s):
		r = Parser()
		for i in s.items:
			if isinstance(i, unicode):
				x = i
			else:
				x = i.copy()
			r.add(x)
		return r

	def empty_render(s):
		return [ColorTag(colors.parser_hint), TextTag('('+s.type.name+')'), EndTag()]

	@property
	def parsed(s):
		#default result:
		r = Bananas(s.items)

		if len(s.items) == 1:
			i0 = s.items[0]
			if isinstance(i0, Node):
				r = i0
			else: 
				assert isinstance(i0, widgets.Text)

				type = s.type
				#if isinstance(s.type, Exp):
				#	type = s.type.type
				#if isinstance(type, Ref):
				#	type = deref_decl(type)
				type = deref_def(type)
				
				
				
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


class ReplParser(Parser):
	menu = []
	def render(s):
		log("ReplParser")
		if len(s.items) == 0: # no items, show the gray type hint
			return s.empty_render()

		for i, item in enumerate(s.items):
			yield [
				AttTag(Att.item_index, (s, i)),
				ElementTag(item),
				EndTag()]

		#yield str(len(s.menu))



class ParserMenuItem(MenuItem):
	def __init__(s, notes, value:Node, score = None):
		super(ParserMenuItem, s).__init__()
		s.brackets_color = colors.parser_menu_item_brackets
		if isinstance(value, str):
			value = Text(value)
		s.value = value
		value.parent = s
		s.scores = Dotdict({
			"@context" : "http://koo5.github.com/lemon/menu",
			"@type" : "Item"
		})
		if isinstance(score, dict):
			for k,v in iteritems(score):
				s.scores[k] = v
		if score != None:  s.scores.init = score
		s.notes = notes

	@property
	def score(s):
		#print s.scores._dict
		return sum([i if type(i) == int else 0 for i in itervalues(s.scores._dict)])

	def tags(s):
		return [MemberTag('value'), ColorTag(colors.menu_item_extra_info), " - "+str(s.value.__class__.__name__)+' ('+str(s.score)+')', EndTag()]

	def long__repr__(s):
		return object.__repr__(s) + "('"+str(s.value)+"')"

class PaletteMenuItem(ParserMenuItem):
	def __init__(s, notes, value, score=0):
		super().__init__(notes, value, score)
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
				return banana(str(arg) + " ?! ")
			expected_type = s.params[name].type
			if isinstance(expected_type, Ref) and hasattr(arg, 'decl') and isinstance(arg.decl, Ref):
				if not arg.decl.target == expected_type.target:
					log("well this is maybe bad, decl %s of %s != %s" % (arg.decl, arg, expected_type))
					return banana(str(arg.decl.name) + " != " + str(expected_type.name))
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
		s.args = dict([(name, Parser()) for name, v in iteritems(s.target.params)]) #this should go to fresh(?)
		s.fix_parents()

	def copy(s):
		r = s.__class__(s.target)
		for k,v in s.args.items():
			r.args[k] = v.copy()
		r.fix_parents()
		return r

	@property
	def slots(s):
		return s.target.params

	def child_type(s, ch):
		for k,v in iteritems(s.slots):
			if s.args[k] == ch:
				return v
		assert False

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


# endregion


class CompoundNodeDef(Syntaxed):
	instance_class = CompoundNode
	def inst_fresh(s, decl=None):
		""" fresh creates default children"""
		return CompoundNode(s)

		


grammar = None

def make_root():
	global grammar
	grammar =  __import__("grammar")

	r = Root()

	build_in_editor_structure_nodes()
	build_in_lemon_language()
	build_in_misc()

	#for k,v in iteritems(B._dict):
	#	log(k, v)


	r['welcome'] = Comment("Press F1 to cycle the sidebar!")

	r["intro"] = B.builtinmodule.inst_fresh()
	r["intro"].ch.statements.items = [
		Comment("""

	the ui of lemon is currently conciped like this:
	root is a dictionary with keys like "intro", "some program" etc.
	it's values are mostly modules. modules can be collapsed and expanded and they
	hold some code or other stuff in a Statements object. This is a text literal inside a module, too.

	Lemon can't do much yet. You can add function calls and maybe define functions. If you are lucky,
	ctrl-del will delete something. Inserting of nodes happens in the Parser node. it looks like this:"""),
		Parser(),
		Comment("If cursor is on a parser, a menu will appear in the sidebar. you can scroll and click it. have fun."),
		Comment("todo: working editor, smarter menu, better parser, real language, fancy projections...;)")
	]

	r["intro"].ch.statements.view_mode = 0


	r["repl"] = B.builtinmodule.inst_fresh()
	r["repl"].ch.statements.parser_class                                                                                                             = ReplParser
	r["repl"].ch.statements.items = [ReplParser()]
	r["repl"].ch.statements.newline()
	r["repl"].ch.statements.view_mode=2


	r["empty module"] = B.modulethatdoesntseeanythingexceptunhide.inst_fresh()
	r["empty module"].ch.statements.view_mode = 2
	uh = B.unhidenode.inst_fresh()
	uh.ch.what.view_mode = 2
	uh.ch.what.add(Text("functioncall"))
	uh.ch.what.add(Text("builtins"))

	r["empty module"].ch.statements.items = [uh, Parser()]

	r["cli dummy empty module"] = B.modulethatdoesntseeanythingexceptunhide.inst_fresh()

	r["builtins"] = B.builtinmodule.inst_fresh()
	r["builtins"]._name = "builtins"
	r["builtins"].ch.statements.items = list(itervalues(B._dict))
	assert len(r["builtins"].ch.statements.items) == len(B) and len(B) > 0
	log("built in %s nodes",len(r["builtins"].ch.statements.items))
	r["builtins"].ch.statements.add(Comment("---end of builtins---"))
	r["builtins"].ch.statements.view_mode = 0


	#r["loaded program"] = B.module.inst_fresh()
	#r["loaded program"].ch.name = Text("placeholder")
	#r["loaded program"].ch.statements.view_mode=0

	r["clipboard"] = B.module.inst_fresh()
	r["clipboard"].ch.name = Text("clipboard")
	r["clipboard"].ch.statements.view_mode=1


	library = r["library"] = make_list('module')
	library.view_mode = 0#library.vm_multiline

	import glob
	for file in glob.glob("library/*.lemon.json"):
		placeholder = library.add(new_module())
		placeholder.ch.name.pyval = "placeholder for "+file
		print(load_module(file, placeholder))
	#todo: walk thru weakrefs to serialized, count successful deserializations, if > 0 repeat?

	def load_txt_module(filename, module):
		text = open(filename).read()
		items = text.split('\n-----\n')
		for idx,i in enumerate(items):
			p = Parser()
			module.ch.statements.add(p)
			p.add(widgets.Text(p, i))

	for file in glob.glob("library/*.lemon.txt"):
		mo = library.add(new_module())
		mo.ch.name.pyval = file
		print(load_txt_module(file, mo))


	#essentials = [x.ch.statements for x in library.items if x.ch.name.pyval == "essentials"][0]
	#r.essentials.banana = essentials.by_name('Banana')



	r["liki"] = B.likimodule.inst_fresh()
	r["liki"].ch.statements.newline()
	r["liki"].ch.statements.view_mode=2
	r["liki"].ch.file.pyval = "liki.lemon.json"
	load_module("liki.lemon.json", r["liki"])





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

	update_syntaxes(r["repl"].scope())
	return r




def update_syntaxes(scope):
	syntax_definitions = []
	for i in scope:
		logging.getLogger("update_syntaxes").debug(i.tostr())
		if isinstance(i, SyntaxedNodecl):
			i.clear_syntaxes()
		if i.ddecl == B.translation:
			syntax_definitions.append(i)
	for i in syntax_definitions:
		dd = deref_decl(i.ch.target)
		dd._additional_syntaxes.append(Syntax(i.ch.tags.pyval, i.to_rendering_tags))



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
				   ["module", ChildTag("name"), ', from file', ChildTag("file"), ":\n", ChildTag("statements"),  TextTag("end.")],
				   {'statements': B.statements,
				    'name': B.text,
				    'file': B.text
				    }))

	build_in(
	SyntaxedNodecl(BuiltinModule,
				   [ChildTag("statements")],
				   {'statements': B.statements,
				    }))


	build_in(
	SyntaxedNodecl(LikiModule,
	               [ChildTag("statements")],
	               {'statements': B.statements,
	                'file': B.text
	                }))


	build_in(
	SyntaxedNodecl(ModuleThatDoesntSeeAnythingExceptUnhide,
	               [ChildTag("statements")],
	               {'statements': B.statements
	                }))

def build_in_lemon_language():

	build_in(Comment(
	"""We start by declaring the existence of some types (decls).
	Once declared, we can reference them from lemon objects.
	Internally, each declaration is a Nodecl object.
	The type name is usually a lowercased
	name of the python class that implements it."""))


	build_in(VarRefNodecl(), 'varref')

	build_in([Nodecl(x) for x in [Number, Bananas, Identifier, RestrictedIdentifier]])

	build_in(Nodecl(List), "list_literal")

	build_in([
		SyntaxedNodecl(WorksAs,
					   [ChildTag("sub"), TextTag(" works as "), ChildTag("sup")],
					   {'sub': 'type', 'sup': 'type'}),

		SyntacticCategory({'name': Text("expression")})
	])


	build_in(SyntaxedNodecl(BindsTighterThan,
				[[ChildTag("a"), " binds tighter than ",  ChildTag("b")]],
				{'a': 'type', 'b': 'type'}))


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
				    'options': B.list_of_anything}))
				   #'options': list_of('text')}))

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

	class HideNode(Syntaxed):
		pass
	class HideExceptNode(Syntaxed):
		pass
	class UnhideNode(Syntaxed):
		pass

	build_in(SyntaxedNodecl(HideNode,
				   ["hide", " ", ChildTag("what")],
				   {'what': 'text'}))

	build_in(WorksAs.b("hidenode", "statement"), False)

	build_in(SyntaxedNodecl(HideExceptNode,
				   ["hide", " ", ChildTag("what"), " ", "except", " ", ChildTag("exceptions")],
				   {'what': 'text',
				    'exceptions': list_of(B.text)}))

	build_in(WorksAs.b("hideexceptnode", "statement"), False)

	build_in(SyntaxedNodecl(UnhideNode,
				   ["unhide ",ChildTag("what")],
				   {'what': list_of(B.text)}))

	build_in(WorksAs.b("unhidenode", "statement"), False)

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
					[TextTag("if "), ChildTag("condition"), ":\n", ChildTag("statements")],

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


	#and a custom node syntax type

	class ParameterTranslation(Syntaxed):
		pass

	class ParameterAsIs(Syntaxed):
		pass

	class Translation(Syntaxed):
		def to_rendering_tags(s):
			r= []
			for i in s.ch.translation:
				if isinstance(i, Text):
					a = i.pyval
				elif isinstance(i, ParameterTranslation):
					pass#todo
				elif isinstance(i, ParameterAsIs):
					pass#todo
				r.append(a)
			return r

	build_in(SyntaxedNodecl(ParameterTranslation,
	                        [ChildTag("new"), TextTag(" - "), ChildTag("old")],
	                        {'new': B.text,
	                         'old': B.text}))
	build_in(SyntaxedNodecl(ParameterAsIs,
	                        [ChildTag("parameter")],
	                        {'parameter': B.text}))
	tmp = B.union.inst_fresh()
	tmp.ch["items"].add(Ref(B.text))
	tmp.ch["items"].add(Ref(B.parametertranslation))
	tmp.ch["items"].add(Ref(B.parameterasis))
	build_in(Definition({'name': Text('custom syntax item'), 'type': tmp}))
	build_in(Definition({'name': Text('custom syntax list'), 'type':list_of(B.custom_syntax_item)}))

	build_in(SyntaxedNodecl(Translation,
				   [ChildTag("tags"), TextTag(" translation of "), ChildTag("syntaxed_nodecl"), TextTag(":\n"), ChildTag("translation")],
					{'tags': list_of(B.text),
					 'syntaxed_nodecl': B.type,
					 'translation': B.custom_syntax_list
					 }))
	build_in(WorksAs.b("translation", "statement"), False)
	build_in(WorksAs.b("custom syntax list", "expression"), False)

	#tmp = b['list'].make_type({'itemtype': Ref(b['union of function signature item types'])})
	#tmp = b['list'].make_type({'itemtype': Ref(b['union of custom syntax item types'])})


	build_in(SyntaxedNodecl(FunctionDefinition,
				   [TextTag("def "), ChildTag("sig"), TextTag(":\n"), ChildTag("body")],
				   #[TextTag("def "), ChildTag("sig"), TextTag(":"), MaybeWhitespace() , TextTag("\n"), MaybeWhitespace(), ChildTag("body")],
					{'sig': B.function_signature_list,
					 'body': B.statements}))

	build_in(WorksAs.b("functiondefinition", "statement"), False)


	#user cant instantiate it, but we make a decl anyway,
	#because we need to display it, its in builtins,
	#its just li ke a normal function, FunctionCall can
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




	build_in(SyntaxedNodecl(Serialized,
				   ["failed to deserialize:", ChildTag("last_rendering"), ChildTag("serialization")],
				   {'last_rendering': B.anything,
				    'serialization':dict_from_to('text', 'anything')}))


	build_in(SyntaxedNodecl(CompoundNodeDef,
	                        ["node", ChildTag('name'), "with syntax:", ChildTag("syntax")],
	                        {'name' : B.text,
				   'syntax': B.custom_syntax_list}))

	build_in(Definition({'name': Text('lvalue'), 'type':make_union([Ref(B.identifier), Ref(B.varref)])}))


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
		return banana("deserialize me first")

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
	print ("loading "+file_name)
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
	bad = False
	for i in d.flatten():
		if isinstance(i, Serialized):
			print("deserialization failed:%s"%i)
			bad = True
	if bad:
		print ("...loaded with warnings")
		return "warning"
	else:
		return "ok"





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
	build_in(WorksAs.b("shellcommand", "expression"), False)


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


	#build_in(SyntaxedNodecl(FilesystemPath,
	#			   [[ChildTag("path")],
	#			    [ChildTag("path"), MemberTag("status")]],
	#			   {'path': (B.text)}))

	def b_files_in_dir(dir):
		import os
		for x in os.walk(dir):
			return x[2]
		return []

	BuiltinPythonFunctionDecl.create(b_files_in_dir, [Text("files in"), str_arg()], list_of('text'), "list files in dir", "ls, dir")

	BuiltinPythonFunctionDecl.create(
		b_lemon_load_file, [Text("load"), str_arg()], Ref(B.text), "load file", "open").pass_root = True





	class MorningRule(Syntaxed):
		pass

	build_in(SyntaxedNodecl(MorningRule,
				   [['every morning at ', ChildTag('hours'), ":", ChildTag('minutes'), ':\n', ChildTag('statements')]],
				   {'hours': (B.number), 'minutes': Exp(B.number), 'statements': B.statements}))




"""
BuiltinMenuItem..
class: based on customnode, one level,
how to do views?
add python_env to Module?
"""


"""
class NodeSyntax(Syntaxed):
	pass


build_in(SyntaxedNodecl(NodeSyntax,
			   [ChildTag("language"), "syntax:", ChildTag("syntax")],
			   {'syntax': b['custom syntax list']}))
"""












"""PiType is a kind of node.
PiType has var - a Var
PiType has type - a Exp
PiType has ret - a Exp
PiType has syntax: [Child("var"), ":"
"""

















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


element.Module = Module







"""
build_in(SyntaxedNodecl(Sequence, ['sequence of', ChildTag('min'), 'or more', ChildTag('itemtype')],
                        {'min': 'number', 'itemtype': B.type})
build_in(Definition({'name': Text('statementsbody'), 'type': Sequence({'min': Number(0), 'itemtype': B.statement)))
build_in(SyntaxedNodecl(Statements, ['{', ChildTag('body'), '}'], {'body': B.statementsbody}))


class Sequence(Syntaxed):
	pass

"""
"""
todo: try pre-generating grammar for marpa 
(add sub-rule objects, linearize grammars depth-first up until <reparse tag>,..?
with or without tail, whatever i can get working

plan b: try gf
plan c: avoid need of reparsing, force nonambiguous grammar for identifiers, go back to a solution employing the editor
"""

def register_symbol(s, m):
	"""register symbols and rules"""
	log = logging.getLogger("marpa").debug

	#if isinstance(s, Sequence):
	#	syntax_for_parser = []

	"""
		statement_followed_by_parser = m.symbol('statement_followed_by_parser')
		m.rule('statement_followed_by_parser', statement_followed_by_parser, [B.statement, parser])
		m.sequence('optionally_elements_followed_by_parser', optionally_elements_followed_by_parser, B.anything.symbol, ident_list, m.maybe_whitespace, 0)
		m.sequence('optionally_elements', optionally_elements, B.anything.symbol, ident_list, m.maybe_whitespace, 0)
		r = m.symbol('Statements literal head')
		m.rule('statements literal head', r, [m.maybe_whitespace, m.known_char('{'), m.maybe_whitespace, m.known_char('}')], empty_statements_body_from_parse)
		return r
	"""

	if isinstance(s, Definition):
		m.node_symbols[s] = m.symbol(s.name)
		m.node_rules[s] = m.rule(str(s), m.node_symbols[s], s.ch.type.parsed.symbol(m))
	if isinstance(s, SyntacticCategory):
		m.node_symbols[s] = m.symbol(s.name)
	elif isinstance(s, WorksAs):
		if s in m.node_rules:
			return
		lhs = s.ch.sup.parsed
		rhs = s.ch.sub.parsed
		if not isinstance(lhs, Ref) or not isinstance(rhs, Ref):
			print ("invalid sub or sup in worksas")
			return
		lhs = lhs.target.symbol(m)
		rhs = rhs.target.symbol(m)
		if args.log_parsing:
			log('%s worksas %s\n (%s := %s)'%(s.ch.sub, s.ch.sup, lhs, rhs))
		if lhs != None and rhs != None:
			r = m.rule(str(s), lhs, rhs)
			m.node_rules[s] = r
	elif isinstance(s, (ParametricListType)):
		dd = s.ddecl
		assert isinstance(dd, ParametricNodecl)
		for k,v in iteritems(m.node_symbols):
			if k.eq_by_value_and_python_class(s): #fixme?
				m.node_symbols[s] = v
				return
		item_symbol = deref_decl(s.ch.itemtype).symbol(m)
		if item_symbol == None:
			log = logging.getLogger("marpa").warning("no symbol for %s" % s)
			return
		desc = '%s literal' % s.tostr()
		m.node_symbols[s] = r = m.symbol(desc)
		log("registering %s grammar" % desc)
		optionally_elements = m.symbol('optionally_elements of %s' % desc)
		m.sequence('optionally_elements of %s' % desc, optionally_elements, item_symbol, ident_list, m.known_char(','), 0)
		opening, closing = m.known_char('['), m.known_char(']')
		m.rule('list literal of %s' % desc, r, [opening, optionally_elements, closing], s.instance_class.from_parse)
	elif isinstance(s, (NodeclBase)):
		m.node_symbols[s] = s.instance_class.register_class_symbol(m)
	elif isinstance(s, (Exp)):
		m.node_symbols[s] = B.expression.symbol()
	elif isinstance(s, (Union)):
		lhs = m.node_symbols[s] = m.symbol(str(s))
		for i in s.ch.items:
			rhs = deref_decl(i) .symbol(m)
			m.node_rules[s] = m.rule(str(s)+"<-"+str(i), lhs, rhs)
	else:
		log(("no symbol for", s))





def register_class_symbol(cls, m):
	"""a nodecl calls this for its instance class"""

	log = logging.getLogger("marpa").debug


	if FunctionCall.__subclasscheck__(cls):
		top = m.symbol("function_call")
		for s in m.scope:
			if isinstance(s, FunctionDefinitionBase):
				rhs = []
				for i in s.sig:
					if type(i) == Text:
						a = m.known_string(i.pyval)
					elif isinstance(i, TypedParameter):
						#TypedParameter means its supposed to be an expression
						a = B.expression.symbol(m)
					elif isinstance(i, UnevaluatedArgument):
						a = deref_decl(i.type).class_symbol(m)
					assert a,  i
					rhs.append(a)
					rhs.append(m.syms.maybe_spaces)
				if args.log_parsing:
					log('rhs:%s'%rhs)
					debugname = "call of "+repr(s)
				else:
					debugname=""
				mbol = m.symbol(debugname)
				m.rule(debugname, mbol, rhs, s.marpa_create_call)
				m.rule("call is "+debugname, top, mbol)
		return top

	elif Ref.__subclasscheck__(cls):
		r = m.symbol('ref')
		for i in m.scope:
			if is_type(i):#todo: not just types but also functions and..?..
				rendering = cls.brackets[0]+"*" + i.name + cls.brackets[1]
				debug_name = "ref to"+str(i)
				sym = m.symbol(debug_name)
				m.rule(debug_name + "is a ref", r, sym)
				m.rule(debug_name, sym, m.known_string(rendering), lambda parsed_text,target=i: cls.from_parse(target)) #log("wtf x:%s i:%s", x, i))#
		return r

	elif VarRef.__subclasscheck__(cls):
		r = m.symbol('varref')
		for i in m.scope:
			if isinstance(i, (TypedParameter, UntypedVar)):
				rendering = "$" + i.name
				debug_name = "varref to"+str(i)
				sym = m.symbol(debug_name)
				m.rule(debug_name + "is a varref", r, sym)
				m.rule(debug_name, sym, m.known_string(rendering), cls.from_parse)
		return r


	elif RestrictedIdentifier.__subclasscheck__(cls):
		body_part = m.symbol('body_part')
		allowed = []
		for rng in ['az', 'AZ']:
			allowed.extend([chr(x) for x in range(ord(rng[0]),ord(rng[1])+1)])
		allowed.extend([ch for ch in '_-'])
		for ch in allowed:
			m.rule('restricted_identifier_body_part_is_', body_part, m.known_char(ch))
		r = m.symbol('Identifier')
		m.sequence('identifier is seq of body part', r, body_part, cls.from_parse)
		return r


	elif Identifier.__subclasscheck__(cls):
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


	elif Text.__subclasscheck__(cls):
		"""should exclude double quote from body parts. will this be solved with precedence when we have body part defined in lemon lang?"""
		clsstr = str(cls)
		log("registering "+clsstr+" grammar")
		double_slash = m.known_string('//')
		slashed_end =  m.known_string('/'+cls.brackets[1])
		body_part = m.symbol(clsstr+'_body_part')
		m.rule(clsstr+'_body_part_is_double_slash', body_part, double_slash)
		m.rule(clsstr+'_body_part_is_slashed_end', body_part, slashed_end)
		m.rule(clsstr+'_body_part_is_nonspecial_char', body_part, m.syms.nonspecial_char)
		m.rule(clsstr+'_body_part_is_known_char', body_part, m.syms.known_char)
		body = m.symbol(clsstr+'body')
		m.sequence(clsstr+'_body is seq of body part', body, body_part, join)
		text = m.symbol(clsstr)
		opening =  m.known_string(cls.brackets[0])
		closing =  m.known_string(cls.brackets[1])
		m.rule(clsstr+'_is_[body]', text, [opening, body, closing], cls.from_parse)
		return text


	elif Number.__subclasscheck__(cls):
		log("registering number grammar")
		digit = m.symbol('digit')
		digits = m.symbol('digits')
		for i in [chr(j) for j in range(ord('0'), ord('9')+1)]:
			m.rule(i + "_is_a_digit",digit, m.known_char(i))
		m.sequence('digits_is_sequence_of_digit', digits, digit, join)
		r = m.symbol('number')
		m.rule('number_is_digits', r, digits, (ident, cls))
		return r

	elif Statements.__subclasscheck__(cls):
		("registering Statements grammar")
		optionally_elements = m.symbol('optionally_statements_elements')
		st = m.symbol("statement with whitespace")
		m.rule("statement with whitespace", st, [B.statement.symbol(m), m.syms.maybe_whitespace],lambda x: x[0])
		m.sequence('optionally_statements_elements', optionally_elements, st, ident_list, m.known_char('\n'), 0)
		r = m.symbol('Statements')
		m.rule('statements literal', r, [m.known_char('{'),m.syms.maybe_whitespace, optionally_elements, m.known_char('}')], cls.from_parse)
		return r

	elif List.__subclasscheck__(cls):
		log("registering list grammar")
		optionally_elements = m.symbol('optionally_elements')
		r = m.symbol('list literal')
		opening =  m.known_char('[')
		closing =  m.known_char(']')
		m.sequence('optionally_elements', optionally_elements, B.anything.symbol(m), ident_list, m.known_char(','), 0)
		m.rule('list literal', r, [opening, optionally_elements, closing], cls.from_parse)
		return r

	elif Syntaxed.__subclasscheck__(cls):
		r = m.symbol(cls.__name__)
		ddecl = deref_decl(cls.decl)
		for sy in ddecl.instance_syntaxes:
			cls.rule_for_syntax(m, r, sy, ddecl)
		return r

	log(("no class symbol for", cls))




def scope_after_hiding_and_unhiding(s):
	assert(type(s.parent) != Root)
	local = what_in_my_module_do_i_see(s)
	library = s.module.scope()
	r = library + local
	full = local + what_module_sees(s.module)
	for i in local:
		dd = deref_decl(i.decl)
		if dd == B.hidenode:
			what = i.ch.what.parsed.value
			if what == "everything":
				r = []
			else: raise Exception("not implemented")
		elif dd == B.hideexceptnode:
			what = i.ch.what.parsed.value
			exc = i.ch.exceptions.parsed.pyval
			if what == "everything":
				r = [x for x in r if x.name in exc]
			else: raise Exception("not implemented")
		elif dd == B.unhidenode:
			what = i.ch.what.parsed.pyval
			logging.getLogger("scope").debug("unhide:%s"%what)
			#if what.parsed.eq(Text("everything")):
			#	r = full[:]
			#else:
			for j in full:
				j = j.parsed
				try:
					name = j.name
				except (KeyError, AttributeError):
					logging.getLogger("scope").debug("does not have name:%s"%str(j))
					continue
				if isinstance(j, Module):
					logging.getLogger("scope").debug("considering module %s" % j)
					if (name in what):
						logging.getLogger("scope").debug("unhiding module %s:"%j)
						for k in j.ch.statements.items:
							k = k.parsed
							logging.getLogger("scope").debug("-%s" % k)
							if k not in r:
								r.append(k)

				#elif is_decl(j) and (name in what):
				if  (name in what):
					logging.getLogger("scope").debug("unhiding %s" % j)
					if j not in r:
						r.append(j)
	return r

def collect_modules_seen_by_module(module):
	if module == module.root["builtins"]:
		return [] # builtins dont see anything
	else:
		modules = [module.root["builtins"]]
		for m in module.root['library'].items:
			if not isinstance(m, Module):
				continue
			if module != m:
				modules.append(m)
			#log(module) #log(r)
		return modules


def what_module_sees(module):
	assert isinstance(module, Module)
	r = []
	for m in collect_modules_seen_by_module(module):
		r.append(m)
		for i in m.ch.statements.parsed.items:
			r.append(i.parsed)
	return r

def what_in_my_module_do_i_see(s):
	assert s.parent,     s.long__repr__()
	r = []
	p = s.parent
	r += [p]
	if isinstance(p, Statements):
		r += [x.parsed for x in p.above(s)]
	elif not isinstance(p, Module):
		r += what_in_my_module_do_i_see(p)
	assert(r != None)
	assert_is_flat(r)
	return r

def assert_is_flat(r):
	assert flatten(r) == r

#return s["builtins"].ch.statements.parsed
