import pygame
from collections import OrderedDict
from compiler.ast import flatten
#import weakref


from dotdict import dotdict
from logger import ping, log
import element
import widgets
from menu import MenuItem, InfoMenuItem, HelpMenuItem
import tags
from tags import ChildTag as ch, WidgetTag as w, TextTag as t, NewlineTag as nl, IndentTag as indent, DedentTag as dedent, ColorTag, EndTag, ElementTag, MenuTag
import tags as asstags
asstags.asselement = element

import project
import colors









class val(list):
	"""
	a list of Values
	during execution, results of evaluation of every node is appended, so there is a history visible, and the current value is the last one"""
	def val(self):
		return self[-1]

	def append(self, x):
		assert(isinstance(x, Node))
		super(self, val).append(x)
		return x
	
	def set(self, x):
		"""constants call this"""
		assert(isinstance(x, Node))
		if len(self) > 0 and self[-1] == x:
			pass
		else:
			super(self, val).append(x)
		return x
	
	

class Children(dotdict):
	pass


class Node(element.Element):
	"""a node is more than an element, it keeps track of its children with a dict.
	in the editor, nodes can be cut'n'pasted around on their own
	"""
	def __init__(self):
		super(Node, self).__init__()
		self.color = (0,255,0,255)
		self.ch = Children()
		self.runtime = dotdict()

	def fix_parents(self):
		self._fix_parents(self.ch.values())

	def setch(self, name, item):
		assert(isinstance(name, str))
		assert(isinstance(item, Node))
		item.parent = self
		self.ch[name] = item

	def replace_child(self, child, new):
		assert(child in self.ch.values())
		assert(isinstance(new, Node))
		for k,v in self.children.iteritems():
			if v == child:
				self.children[k] = new
		new.parent = self

	def scope(self):
		r = []

		if isinstance(self.parent, List):
			r += self.parent.above(self)

		r += self.parent.scope()

		assert(r != None)
		assert(flatten(r) == r)
		return r

	def flatten(self):
		assert(isinstance(v, Node) for v in self.ch.itervalues())
		return [self] + [v.flatten() for v in self.ch.itervalues()]

	def eval(self):
		self.runtime.value.append(self._eval())
		return self.runtime.value.val

	def program(self):
		if isinstance(self, Program):
			return self
		else:
			if self.parent != None:
				return self.parent.program()
			else:
				print self, "has no parent"
				return None

	@classmethod
	def fresh(cls, decl):
		r = cls()
		r.decl = decl
		return r

	@classmethod
	def palette(cls, scope):
		return [ColliderMenuItem(cls.make)]



class Syntaxed(Node):
	def __init__(self, kids):
		super(Syntaxed, self).__init__()
		self.syntax_index = 0
		self.check()
		assert(len(kids) == len(self.child_types))
		for k in self.child_types.iterkeys():
			self.setch(k, kids[k])
			#todo: check type

	def check(self):
		assert(isinstance(self.child_types, dict))
		for name, type in self.child_types.iteritems():
			assert(isinstance(name, str))
			assert(isinstance(type, (NodeclBase, Definition, ParametricType))) #what else works as a type?

	@property
	def syntax(self):
		return self.syntaxes[self.syntax_index]

	def render(self):
		return self.syntax

	def prev_syntax(self):
		self.syntax_index  -= 1
		if self.syntax_index < 0:
			self.syntax_index = 0
		log("prev")

	def next_syntax(self):
		self.syntax_index  += 1
		if self.syntax_index == len(self.syntaxes):
			self.syntax_index = len(self.syntaxes)-1
		log("next")

	def on_keypress(self, e):
		if pygame.KMOD_CTRL & e.mod:
			if e.key == pygame.K_PAGEUP:
				self.prev_syntax()
				return True
			if e.key == pygame.K_PAGEDOWN:
				self.next_syntax()
				return True

	@classmethod
	def fresh(cls, decl):
		kids = {}
		#fix:
		for k, v in decl.instance_slots.iteritems(): #for each child:
			#if there is only one possible node type to instantiate..
			if v == b['statements']:
				a = v.inst_fresh()
			else:
				a = NodeCollider(v)
			assert(isinstance(a, Node))
			kids[k] = a
		r = cls(kids)
		r.decl = decl
		return r


	@property
	def syntaxes(self):
		return [self.decl.instance_syntax]
	@property
	def child_types(self):
		return self.decl.instance_slots








class Collapsible(Node):
	"""Collapsible - List or Dict - dont have a title, a top unindented line. They are just
	the items...now"""
	def __init__(self, expanded=True, vertical=True):
		super(Collapsible, self).__init__()	
		self.expand_collapse_button = widgets.Button(self)
		self.expand_collapse_button.push_handlers(on_click=self.on_widget_click)
		self.expanded = expanded
		self.vertical = vertical
	
	def render(self):
		self.expand_collapse_button.text = ("-" if self.expanded else "+")
		return [w('expand_collapse_button')] + [indent()] + (self.render_items() if self.expanded else [nl()]) + [dedent()]
	
	def toggle(self):
		self.expanded = not self.expanded
		if self.expanded:
			print "expand"
		else:
			print "collapse"

	def on_widget_click(self, widget):
		if widget is self.expand_collapse_button:
			self.toggle()

	def _eval(self):
		for i in self.items:
			i.eval()
		return self


class Dict(Collapsible):
	def __init__(self, expanded=True):
		super(Dict, self).__init__(expanded)
		self.items = OrderedDict()
		
	def render_items(self):
		r = []
		for key, item in self.items.iteritems():
			r += [t(key), t(":"), indent(), nl()]
			r += [ElementTag(item)]
			r += [dedent(), nl()]
		return r

	def __getitem__(self, i):
		return self.items[i]

	def __setitem__(self, i, v):
		self.items[i] = v
		v.parent = self

	def fix_parents(self):
		super(Dict, self).fix_parents()
		self._fix_parents(self.items.values())

	def flatten(self):
		return [self] + [v.flatten() for v in self.items.itervalues() if isinstance(v, Node)]
		#skip Widgets, as in settings

	def add(self, (key, val)):
		assert(not self.items.has_key(key))
		self.items[key] = val
		assert(isinstance(key, str))
		assert(isinstance(val, element.Element))
		val.parent = self


class List(Collapsible):
	def __init__(self, expanded=True, vertical=True):
		#if self.item_type ..
		super(List, self).__init__(expanded, vertical)
		self.items = []

	def render_items(self):
		r = []
		for item in self.items:
			r += [ElementTag(item)]
			if self.vertical: r+= [nl()] 
		return r

	def __getitem__(self, i):
		return self.items[i]

	def __setitem__(self, i, v):
		self.items[i] = v
		v.parent = self

	def fix_parents(self):
		super(List, self).fix_parents()
		self._fix_parents(self.items)

	def on_keypress(self, e):
		item_index = self.insertion_pos(e.cursor)
		if e.key == pygame.K_DELETE and e.mod & pygame.KMOD_CTRL:
			if len(self.items) > item_index:
				del self.items[item_index]
		#???
		if e.key == pygame.K_RETURN:
			pos = self.insertion_pos(e.cursor)
			p = NodeCollider(self.types)
			p.parent = self
			self.items.insert(pos, p)
			return True

	def insertion_pos(self, (char, line)):
		i = -1
		for i, item in enumerate(self.items):
			#print i, item, item._render_start_line, item._render_start_char
			if (item._render_start_line >= line and
				item._render_start_char >= char):
				return i
		return i + 1

	def eval(self):
		for i in self.items:
			i.eval()
		self.runtime.evaluated = True
		return self.runtime.value.append(Value([x.runtime.value.val for x in self.items]))
			
	def flatten(self):
		return [self] + [v.flatten() for v in self.items if isinstance(v, Node)]

	def replace_child(self, child, new):
		assert(child in self.items)
		self.items[self.items.index(child)] = new
		new.parent = self

	def add(self, item):
		self.items.append(item)
		assert(isinstance(item, Node))
		item.parent = self

	def newline(self):
		p = NodeCollider(self.item_type)
		p.parent = self
		self.items.append(p)

	@property
	def item_type(self):
		assert(isinstance(self.decl, ParametricType))
		return self.decl.ch.itemtype

	def above(self, item):
		assert(item in self.items)
		r = []
		for i in self.items:
			if i == item:
				return r
			else:
				r.append(i)


class WidgetedValue(Node):
	def __init__(self):
		super(WidgetedValue, self).__init__()	
	@property
	def pyval(self):
		return self.widget.value
	def render(self):
		return [w('widget')]
	@classmethod
	def fresh(cls, decl):
		r = cls("")
		r.decl = decl
		return r


class Number(WidgetedValue):
	def __init__(self, value):
		super(Number, self).__init__()
		self.widget = widgets.Number(self, value)

class Text(WidgetedValue):
	def __init__(self, value):
		super(Text, self).__init__()
		self.widget = widgets.Text(self, value)

class Root(Dict):
	def __init__(self):
		super(Root, self).__init__()
		self.parent = None
		self.post_render_move_caret = 0
		self.indent_length = 4

	def render(self):
		return [ColorTag((255,255,255,255))] + self.render_items() + [EndTag()]

	def scope(self):
		return []


class Module(Syntaxed):
	
	def __init__(self, kids):
		super(Module, self).__init__(kids)

	def add(self, item):
		self.ch.statements.add(item)

	def __getitem__(self, i):
		return self.ch.statements[i]

	def __setitem__(self, i, v):
		self.ch.statements[i] = v





class Ref(Node):
	def __init__(self, target):
		super(Ref, self).__init__()
		self.target = target
	def render(self):
		return [t('*'), w("target")]


b = OrderedDict()

def bi(node):
	"""build in"""
	b[node.name] = node




class ParametricType(Syntaxed):
	def __init__(self, kids, decl):
		self.decl = decl
		super(ParametricType, self).__init__(kids)
	@property
	def child_types(self):
		return self.decl.type_slots
	@property
	def syntaxes(self):
		return [self.decl.type_syntax]
	def inst_fresh(self):
		return self.decl.instance_class.fresh(self)




class NodeclBase(Node):
	#this python class is abstract
	def __init__(self, instance_class):
		super(NodeclBase, self).__init__()
		self.instance_class = instance_class
	def render(self):
		return [t("builtin node type:"), t(str(self.instance_class))]
	@property
	def name(self):
		return self.instance_class.__name__.lower()
	def instantiate(self, kids):
		return self.instance_class(kids)
	def inst_fresh(self):
		return self.instance_class.fresh(self)


class TypeNodecl(NodeclBase):
	def __init__(self):
		super(TypeNodecl, self).__init__(Ref)
		b['type'] = self
	@staticmethod
	def palette(scope):
		decls = [x for x in scope if isinstance(x, (NodeclBase))]
		return [ColliderMenuItem(Ref(x)) for x in decls]


TypeNodecl()


class Nodecl(NodeclBase):
	def __init__(self, instance_class):
		super(Nodecl, self).__init__(instance_class)
		instance_class.decl = self


class SyntaxedNodecl(NodeclBase):
	"""
	child types of Syntaxed are like b["text"], they are "values",
	 children themselves are either Refs (pointing to other nodes),
	 or other instances of Node
	"""
	def __init__(self, instance_class, instance_syntax, instance_slots):
		super(SyntaxedNodecl , self).__init__(instance_class)
		instance_class.decl = self
		self.instance_slots = instance_slots
		self.instance_syntax = instance_syntax
		b[self.name] = self

class ParametricNodecl(NodeclBase):
	"""only non Syntaxed types are parametric now(list and dict),
	so this contains the type instance's syntax and slots"""
	def __init__(self, instance_class, type_syntax, type_slots):
		super(ParametricNodecl, self).__init__(instance_class)
		self.type_slots = type_slots
		self.type_syntax = type_syntax
	def make_type(self, kids):
		return ParametricType(kids, self)









[bi(Nodecl(x)) for x in [Number, Text]]

print b


class AbstractType(Syntaxed):
	"""this is a syntactical category(?) of nodes"""
	def __init__(self, kids):
		super(AbstractType, self).__init__(kids)
SyntaxedNodecl(AbstractType,
               [t("abstract type:"), ch("name")],
               {'name': b['text']})

class IsSubclassOf(Syntaxed):
	"""just a relation"""
	def __init__(self, kids):
		super(IsSubclassOf, self).__init__(kids)

SyntaxedNodecl(IsSubclassOf,
               [ch("sub"), t("is a subclass of"), ch("sup")],
               {'sub': b['type'], 'sup': b['type']})


class Definition(Syntaxed):
	"""should have type functionality"""
	def __init__(self, kids):
		super(Definition, self).__init__(kids)
		b[self.ch.name.pyval] = self
		print b
	def inst_fresh(self):
		return self.ch.type.inst_fresh()

SyntaxedNodecl(Definition,
               [t("define"), ch("name"), t("as"), ch("type")], #expression?
               {'name': b['text'], 'type': b['type']})



b['statement'] = AbstractType({'name': Text("statement")})
b['expression'] =AbstractType({'name': Text("expression")})
b[0] = IsSubclassOf({'sub': Ref(b["expression"]), 'sup': Ref(b["statement"])})
#b[1] = IsSubclassOf([Ref(b["number"]), Ref(b["expression"])])
#b[2] = IsSubclassOf([Ref(b["somethingnew"]), Ref(b["expression"])])


b['list'] = ParametricNodecl(List,
                 [t("list of"), ch("itemtype")],
                 {'itemtype': b['type']})
b['dict'] = ParametricNodecl(Dict,
                 [t("dict from"), ch("keytype"), t("to"), ch("valtype")],
                 {'keytype': b['type'], 'valtype': b['type']})


#IsSubclassOf([Ref(b["list"]), Ref(b["expression"])])
#IsSubclassOf([Ref(b["dict"]), Ref(b["expression"])])


Definition({'name': Text("statements"), 'type': b['list'].make_type({'itemtype': b['statement']})})

b['module'] = SyntaxedNodecl(Module,
               [t("module:"), nl(), ch("statements"), t("end.")],
               {'statements': b['statements']})

Definition({'name': Text("list of types"), 'type': b['list'].make_type({'itemtype': b['type']})})

class Union(Syntaxed):
	def __init__(self, children):
		super(Union, self).__init__(children)

b['union'] = SyntaxedNodecl(Union,
               [t("union of"), ch("items")],
               {'items': b['text'], 'type': b['list'].make_type({'itemtype': b['type']})})
b['union'].notes="""should be just "type or type or type...",
                 but Syntaxed with a list is an easier implementation for now"""





def test_root():
	r = Root()
	r.add(("program", b['module'].inst_fresh()))
	r["program"].ch.statements.newline()
	r.add(("builtins", b['module'].inst_fresh()))
	r["builtins"].ch.statements.items = list(b.itervalues())
	return r




class NodeCollider(Node):
	def __init__(self, type):
		super(NodeCollider, self).__init__()
		self.type = type
		self.items = []
		self.add(Text(""))

	def render(self):
		r = [t("[")]
		for item in self.items:
			r += [ElementTag(item)]
		r += [t("]")]
		return r

	def __getitem__(self, i):
		return self.items[i]

	def fix_relations(self):
		super(NodeCollider, self).fix_relations()
		self.fix_(self.items)

	def on_keypress(self, e):
		item_index = self.insertion_pos(e.cursor)
		if e.key == pygame.K_DELETE and e.mod & pygame.KMOD_CTRL:
			if len(self.items) > item_index:
				del self.items[item_index]

	def insertion_pos(self, (char, line)):
		i = -1
		for i, item in enumerate(self.items):
			#print i, item, item._render_start_line, item._render_start_char
			if (item._render_start_line >= line and
				item._render_start_char >= char):
				return i
		return i + 1

	def flatten(self):
		return [self] + [v.flatten() for v in self.items if isinstance(v, Node)]

	def add(self, item):
		self.items.append(item)
		assert(isinstance(item, Node))
		item.parent = self

	def replace_child(self, child, new):
		assert(child in self.items)
		self.items[self.items.index(child)] = new
		new.parent = self
		#add a blank at the end
		p = SomethingNew()
		p.parent = self
		self.items.append(p)

	def eval(self):
		i = self.items[0]
		i.eval()
		self.runtime = i.runtime
		return self.runtime.value.val

	def menu(self):
		scope = self.scope() + self.root["builtins"].ch.statements.items #all nodes
		nodecls = [x for x in scope if isinstance(x, NodeclBase)]

		menu = flatten([x.palette() for x in nodecls])

		#ev = self.slot.evaluated
		type = self.type #self.slot.type

		#slot type is Nodecl or Definition or AbstractType or ParametrizedType
		#first lets search for things in scope that are already of that type
		#for i in menu:
		#	if i.value.decl.eq(type):
		#		v.score += 1

		return menu

# hack here, to make a menu item renderable by project.project
#i think ill redo the screen layout as two panes of projection
class ColliderMenuItem(MenuItem):
	def __init__(self, value):
		self.value = value
		self.score = 0
		self.brackets_color = (0,0,255)
		#(and so needs brackets_color)

	#PlaceholderMenuItem is not an Element, but still has tags(),
	#called by project.project called from draw()
	def tags(self):
		return [ColorTag((0,255,0)),w('value'), t(" - "+str(self.value.__class__.__name__)), EndTag()]
		#and abusing "w" for "widget" here...not just here...

	def draw(self, menu, s, font, x, y):
		#replicating draw_root, but for now..
		#project._width = ..
		lines = project.project(self)
		area = pygame.Rect((x,y,0,0))
		for row, line in enumerate(lines):
			for col, char in enumerate(line):
				chx = x + font['width'] * col
				chy = (y+2) + font['height'] * row
				sur = font['font'].render(
					char[0],False,
					char[1]['color'],
					colors.bg)
				s.blit(sur,(chx,chy))
				area = area.union((chx, chy, sur.get_rect().w, sur.get_rect().h+2))
		return area













#todo function arguments:#mode = eval/pass, untyped argument,
#todo optional function return type
#todo: show and hide argument names. syntaxed?

class TypedArgument(Syntaxed):
	def __init__(self, kids):
		super(TypedArgument, self).__init__(kids)

SyntaxedNodecl(TypedArgument,
               [ch("name"), t("-"), ch("type")],
               {'name': b['text'], 'type': b['type']})

tmp = b['union'].inst_fresh()
tmp.ch["items"].add(Ref(b['text']))
tmp.ch["items"].add(Ref(b['typedargument']))
Definition({'name': Text('function signature items'), 'type': tmp})

tmp = b['list'].make_type({'itemtype': Ref(b['function signature items'])})
Definition({'name': Text('function signature list'), 'type':tmp})




class FunctionDefinitionBase(Syntaxed):

	def __init__(self, kids):
		super(FunctionDefinitionBase, self).__init__(kids)
	@property
	def arg_types(selfs):
		args = [i for i in self.sig.items if isinstance(i, TypedArgument)]
		return [i.ch.type for i in args]
	@property
	def sig(self):
		return self.ch.sig

class FunctionDefinition(FunctionDefinitionBase):

	def __init__(self):
		super(FunctionDefinition, self).__init__()

SyntaxedNodecl(FunctionDefinition,
               [t("deffun:"), ch("sig"), t(":\n"), ch("body")],
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
		r = [t('(call)')]
		for i in self.definition.signature.items:
			if isinstance(i, Text):
				r += [t(i.widget.text)]
			elif isinstance(i, ArgumentDefinition):
				r += [ElementTag(self.arguments.items[i])]

		return r
"""


"""
class PythonFunctionDecl(Syntaxed):
	def __init__(self, fun, sig, arg):
		self.setch('signature', FunctionSignature(sig))


PythonFunctionDecl(
	operator.div,
	signature = [ad("left"), tl("/"), ad("right")],
	arg_types = {'left': b['expression'], 'right': b['expression']})
"""


class BuiltinFunctionDecl(FunctionDefinitionBase):
	def __init__(self, kids):
		super(BuiltinFunctionDecl, self).__init__(kids)
	@staticmethod
	def create(name, fun, sig):
		x = BuiltinFunctionDecl.fresh()#mkay only parametric nedds to pass decl?
		b[name] = x
		x.ch.name.widget.value = name
		x.fun = fun
		x.ch.sig.items = sig


SyntaxedNodecl(BuiltinFunctionDecl,
               [t("builtin function"), ch("name"), t(":"), ch("sig")],
				{'sig': b['function signature list'],
				 'name': b['text']})

def multiply_eval(args):
		l,r = args.left.eval(), args.right.eval()
		assert(isinstance(l, Value))
		assert(isinstance(r, Value))
		res = Value(b['number'], l.value * r.value)
		return res

BuiltinFunctionDecl.create("multiply",
                           multiply_eval,
	[	TypedArgument({'name': Text("left"), 'type': Ref(b['number'])}),
		Text("*"),
		TypedArgument({'name': Text("right"), 'type': Ref(b['number'])})])



class FunctionCall(Node):
	def __init__(self, target):
		super(FunctionCall, self).__init__()
		assert isinstance(target, FunctionDefinition)
		self.target = target
		self.args = [NodeCollider(v) for v in self.target.arg_types]
		self._fix_parents(self.args)
	"""
	def replace_child(self, child, new):
		x = self.args.find(child)
		self.args[x] = new
		new.parent = self
	"""
	def render(self):
		r = [t('!')]
		for i, v in enumerate(self.target.sig):
			if isinstance(v, Text):
				r += [t(v.pyval)]
			elif isinstance(v, TypedArgument):
				r += [ElementTag(self.args[i])]
		return r

	@staticmethod
	def palette(scope):
		defuns = [x for x in scope if isinstance(x,(BuiltinFunctionDecl, FunctionDefinition))]
		return [ColliderMenuItem(FunctionCall(x)) for x in defuns]
