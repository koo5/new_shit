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

		if isinstance(self.parent, Statements):
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
	def fresh(cls, type):
		r = cls()
		r.type = type
		return r


class Syntaxed(Node):
	def __init__(self, children):
		super(Syntaxed, self).__init__()
		self.syntax_index = 0
		self.check()
		assert(len(children) == len(self.child_types))
		for i,k,v in enumerate(self.child_types.iteritems()):
			#todo: check
			self.setch(k, children[i])

	def check(self):
		assert(isinstance(self.child_types, dict))
		for name, types in self.child_types.iteritems():
			assert(isinstance(name, str))
			assert(isinstance(types, list))
			for t in types:
				assert(isinstance(t, (BuiltinNodeDecl, Type)))
		
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
	def fresh(cls, type):
		kids = []
		#fix:
		for k, v in cls.child_types.iteritems(): #for each child:
			#if there is only one possible node type to instantiate..
			if v[0] == b['statements']:
				a = Statements()
			else:
				a = NodeCollider(v)
			kids.append(a)
		r = cls(kids)
		r.type = type
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
	def __init__(self, type, expanded=True, vertical=True):
		super(List, self).__init__(expanded, vertical)
		self.type = type
		assert(isinstance(type, ParametricType))
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
		p = NodeCollider(self.types)
		p.parent = self
		self.items.append(p)

	@property
	def item_type(self):
		return self.type.ch.item_type



class SomethingNew(Node):
	def __init__(self, text):
		super(SomethingNew, self).__init__()
		self.text = text
	def render(self):
		return [t("?"),t(self.text), t("?")]

class WidgetedValue(Node):
	def __init__(self):
		super(WidgetedValue, self).__init__()	
	def pyval(self):
		return self.widget.value
	def render(self):
		return [w('widget')]

class Number(WidgetedValue):
	def __init__(self, value):
		super(Number, self).__init__()
		self.widget = widgets.Number(self, 555)

class Statements(List):
	def __init__(self):
		List.__init__(self, type=[b['statement']], expanded=True, vertical=True)

	@property
	def item_type(self):
		return b['statement']

	def above(self, item):
		assert(item in self.items)
		r = []
		for i in self.items:
			if i == item:
				return r
			else:
				r.append(i)


class Root(Dict):
	def __init__(self):
		super(Root, self).__init__()
		self.parent = None
		self.post_render_move_caret = 0
		self.indent_length = 4

	def render(self):
		return [ColorTag((255,255,255,255))] + self.render_items() + [EndTag()]

class Module(Syntaxed):
	
	def __init__(self, children):
		super(Module, self).__init__()
		self.name = widgets.Text(self, name)

	def add(self, item):
		self.ch.statements.add(item)

	def __getitem__(self, i):
		return self.ch.statements[i]

	def __setitem__(self, i, v):
		self.ch.statements[i] = v















b = {}


class SimpleType(Node):
	def __init__(self, decl):
		super(SimpleType, self).__init__()
		self.decl = decl
	def render(self):
		return [t(self.name)]
	def make_inst(self):
		return self.decl.instance_class.fresh(self)

class ParametricType(Syntaxed):
	def __init__(self, decl):
		super(ParametricType, self).__init__()
		self.decl = decl
	def make_inst(self):
		return self.decl.instance_class.fresh()
	@property
	def child_types(self):
		return self.decl.type_slots
	@property
	def syntaxes(self):
		return [self.decl.type_syntax]



#abstract
class BuiltinTypeDecl(Node):
	def __init__(self, instance_class):
		super(BuiltinTypeDecl , self).__init__()
		self.instance_class = instance_class
		b[self.name] = self
	def render(self):
		return [t("builtin type:"), t(str(self.instance_class))]
	@property
	def name(self):
		return self.instance_class.__class__.__name__.lower()

class BuiltinSimpleTypeDecl(BuiltinTypeDecl):
	def make_type(self):
		return SimpleType(self)

class BuiltinSyntaxedTypeDecl(BuiltinTypeDecl):
	def __init__(self, instance_class, instance_slots, instance_syntax):
		super(BuiltinSyntaxedTypeDecl , self).__init__(instance_class)
		self.instance_slots = instance_slots
		self.instance_syntax = instance_syntax
	def make_type(self):
		return SimpleType(self)

class BuiltinParametricTypeDecl(BuiltinTypeDecl):
	"""only non Syntaxed types are parametric (just list and dict),
	so this contains the type instance's syntax and slots"""
	def __init__(self, instance_class, type_slots, type_syntax):
		super(BuiltinParametricTypeDecl , self).__init__(instance_class)
		self.type_slots = type_slots
		self.type_syntax = type_syntax
	def make_type(self):
		return ParametricType(self)







(BuiltinSimpleTypeDecl(x) for x in [Number, SomethingNew, Statements])


BuiltinParametricTypeDecl(List,
                          [t("list of"), ch("itemtype")],
                          {'itemtype': b['type']})
BuiltinParametricTypeDecl(Dict,
                          [t("dict from"), ch("keytype"), t("to"), ch("valtype")],
                          {'keytype': b['type'], 'valtype': b['type']})



BuiltinSyntaxedTypeDecl(Module,
                         [t("module:"), nl(), ch("statements"), t("end.")],
                         {'statements': [b['statements']]})


"""
class BaseType(Node):
	def __init__(self):
		super(BaseType, self).__init__()
		b['base type'] = self
BaseType()
"""

class AbstractType(Node):
	def __init__(self, name):
		super(AbstractType, self).__init__()
		b[name] = self

class IsSubclassOf(Node):
	def __init__(self, sub, sup):
		super(IsSubclassOf, self).__init__()
		b[self] = self
		self.sup = sup
		self.sub = sub


AbstractType("statement")
AbstractType("expression")

IsSubclassOf(b["expression"], b["statement"])
IsSubclassOf(b["number"], b["expression"])
IsSubclassOf(b["somethingnew"], b["expression"])
IsSubclassOf(b["list"], b["expression"])
IsSubclassOf(b["dict"], b["expression"])

"""
x = b['list'].make_type()
x.setch('itemtype', b['statement'])
BuiltinSubclass("statements", x)
"""




def test_root():
	r = Root()
	r.add(("program", b['module'].make_type().make_inst()))
	r["program"].ch.statements.newline()
	r.add(("builtins", b['module'].inst().inst()))
	r["builtins"].ch.statements.items = list(b)


"""


def test_root():
	r = Root()
	r.add(("programs", ListType((ProgramType)).inst()))
	r["programs"].add(Program())
	r["programs"][0].ch.statements.newline()
	r.add(("modules", 




class VariableDecl(Syntaxed):
	def __init__(self, (kids)):
		self.child_types = {'name': b['text'],
	 						'type': b['type']}
		super(VariableDecl, self).__init__()
	
class Union(Syntaxed):
	syntaxes == [[ch("l"), t("or"), ch("r")]]
	doc = "only two nodes for now, sorry"
	def __init__(self, children):
		self.child_types = {'l': b['type'], 'r': b['type']}
		super(Union, self).__init__(children)


BuiltinNodeType('union', Union)
Subclass(b['union'], b['type'])

Definition('function signature list', 
b['list'].instance((b['union'].instance((Ref(b['text']), Ref(b['argument']_____






 {'of': b['union











b['type'] = TypeType()

class TypeType(
	name = 'type'
	
for each declaration in scope
	if declaration.isinstanceof(
















<function returning <int>>
a is a <list of <ints>>



function arguments:
mode = eval/pass
"""


