#nodes.py isnt used, the new version is typed.py


#everything is lumped together here, real ast nodes with clock and sticky notes,
#tho some nodes broke away into toolbar.py settings.py and the_doc.py
#a node is more than an element, it keeps track of its children with a dict.
#in the editor, nodes can be cut'n'pasted around on their own, which wouldnt
#make sense for widgets


import pygame

from collections import OrderedDict
from compiler.ast import flatten
#import weakref



from dotdict import dotdict
from lemon_logger import ping, log
import element
import widgets
from menu import MenuItem, InfoMenuItem, HelpMenuItem
import tags
from tags import *
import tags
tags.asselement = element
import project
import colors




b = {}







class val(list):
	"""
	a list of Values
	during execution, results of evaluation of every node is appended, so there is a history visible, and the current value is the last one"""
	def val(self):
		return self[-1]

	def append(self, x):
		assert(isinstance(x, Value))
		superval, self).append(x)
		return x
		

class Children(dotdict):
	pass


class Node(element.Element):
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




#WithDef uses another object, SyntaxDef
class SyntaxDef(Node):
	def __init__(self, syntax_def):
		super(SyntaxDef, self).__init__()
		self.syntax_def = syntax_def

	def render(self):
		return [t("syntax definition:"), t(str(self.syntax_def))]

class WithDef(Node):
	def __init__(self):
		super(WithDef, self).__init__()
		self.syntax_def

	def render(self):
		self.syntax_def = self.root.find("modules/0/0")
		assert(isinstance(self.syntax_def, SyntaxDef))
		return self.syntax_def.syntax_def


#Syntaxed has syntaxes as part of class definition

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
				assert(isinstance(t, (BuiltinNodeDecl, TypeRef)))

	@classmethod
	def new(cls):
		r = cls()
		if len(types) == 1 and types[0] == b['statements']:
			#, 'Dict', 'List']:
			v = Statements()
		else:
			v = NodeCollider(types)
		self.ch[name] = v
		
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
	def new(cls):
		r = cls()
		for k, v in cls.child_types.iteritems():
			if v[0] == b['statements']:
				x = Statements()
			else:
				 x = NodeCollider(v)
			r.children[k] = x





class TypeRef(Node):
	def __init__(self, target):
		self.target = target
		assert(isinstance(target, (BuiltinTypeDecl, Subclass)))





class BuiltinTypeDecl(Node):
	def __init__(self, name):
		super(BuiltinTypeDecl, self).__init__()
		self.name = name

	def render(self):
		return [t("builtin type:"), t(name)]




class BuiltinNodeDecl(Node):
	def __init__(self, cls):
		super(BuiltinNodeDecl, self).__init__()
		self.cls = cls

	def render(self):
		return [t("builtin node declaration:"), t(str(self.cls))]


class BuiltinTypeDecl(Node):
	def __init__(self, name):
		self.name = name

class Value(object):
	#type, pyval
	def _eval(self):
		return self
	pass
	
class WidgetedValue(Node):
	def __init__(self):
		super(WidgetedValue, self).__init__()	
	def pyval(self):
		return self.widget.value
	def render(self):
		return [w('widget')]

class TextVal(WidgetedValue):
	def __init__(self, value):
		super(TextVal, self).__init__()
		self.type = TypeRef(b['text'])
		self.widget = widgets.Text(self, "")
class NumberVal(WidgetedValue):
	def __init__(self, value):
		super(NumberVal, self).__init__()
		self.type = TypeRef(b['number'])
		self.widget = widgets.Number(self, 0)


class BoolVal(WidgetedValue):
	def __init__(self, value):
		super(BoolVal, self).__init__()
		self.type = TypeRef(b['bool'])
		self.widget = widgets.Toggle(self, False)
	def render(self):
		return [w('widget')]












class Collapsible(Value):
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


class DictVal(Collapsible):
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


class ListVal(Collapsible):
	def __init__(self, types=['all'], expanded=True, vertical=True):
		super(List, self).__init__(expanded, vertical)
		self.types = types
		assert(isinstance(types, list))
		for i in types:
			assert(isinstance(i, str))
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

"""
bs["listval"] = BuiltinTypeDef([t("list of"), ch("itemtype")], {"itemtype": b[TypeRef]})
bs["intval"] = BuiltinTypeDef([t("int")])
bs["textval"] = BuiltinTypeDef([t("text")])
"""

class Statements(ListVal):
	def __init__(self):
		List.__init__(self, types=[TypeRef(b['statement'])], expanded=True, vertical=True)

	def above(self, item):
		assert(item in self.items)
		r = []
		for i in self.items:
			if i == item:
				return r
			else:
				r.append(i)



class Root(DictVal):
	def __init__(self):
		super(Root, self).__init__()
		self.parent = None
		self.post_render_move_caret = 0
		self.indent_length = 4

	def render(self):
		return [ColorTag((255,255,255,255))] + self.render_items() + [EndTag()]



class SomethingNew(Node):
	def __init__(self, text):
		super(SomethingNew, self).__init__()
		self.text = text
	def render(self):
		return [t("?"),t(self.text), t("?")]







class Module(Syntaxed):
	syntaxes = [[t("module"), w("name"), nl(), ch("statements"), t("end.")]]

	def __init__(self, name="unnamed"):
		self.child_types = {'statements': [b['statements']]}
		super(Module, self).__init__()
		self.name = widgets.Text(self, name)

	def add(self, item):
		self.ch.statements.add(item)

	def __getitem__(self, i):
		return self.ch.statements[i]

	def __setitem__(self, i, v):
		self.ch.statements[i] = v


#r['program'].syntax_def = root.find('modules/items/0/statements/items/0')
#assert(isinstance(r['program'].syntax_def, SyntaxDef))
class Program(Syntaxed):
	syntaxes = [[t("program by "), ch("author"), nl(), ch("statements"), t("end."), w("run_button"), w("results")]]

	def __init__(self):
		self.child_types = {
					'statements': [b['statements']],
					'name': [b['text']],
					'author': [b['text']]}

		super(Program, self).__init__()
		#self.sys=__import__("sys")

		self.run_button = widgets.Button(self, "run!")
		self.run_button.push_handlers(on_click = self.on_run_click)
		self.results = widgets.Text(self, "")
		
	def on_run_click(self, widget):
		self.run()

	def menu(self):
		return [HelpMenuItem("f5: run")]

	def on_keypress(self, e):
		if e.key == pygame.K_F5:
			self.run()
			return True
	
	def run(self):
		for i in self.root.flatten():
			i.runtime.clear()
			i.runtime.value = val()
		
		self.results.text = ' Results:"' + str(self.eval()) + '"'
	
	def eval(self):
		self.runtime.evaluated = True
		return self.statements.eval()
		
	def scope(self):
		r = []
		for m in self.root.find("modules/items"):
			if isinstance(m, Module):
				r += m.find("statements/items")
		return r

	def add(self, item):
		self.statements.add(item)


class ShellCommand(Syntaxed):
	syntaxes = [[t("run shell command:"), w("command")]]

	def __init__(self, command):
		super(ShellCommand, self).__init__()
		self.command = widgets.Text(self, command)


class Note(Syntaxed):
	def __init__(self, text=""):
		super(Note,self).__init__()
		self.syntaxes = [[t("note: "), w("text")]]
		self.text = widgets.Text(self, text)

class Todo(Note):
	def __init__(self, text="", priority = 1):
		super(Todo,self).__init__(text)
		self.syntaxes = [[ColorTag(self.color), t("todo:"), EndTag(), w("text"), w("priority_widget")]]
		self.text = widgets.Text(self, text)
		self.priority_widget = widgets.Number(self, priority)
		self.priority_widget.push_handlers(
			on_change=self.on_priority_change)
		self.on_priority_change("whatever")

	@property
	def priority(self):
		return self.priority_widget.value

	def on_priority_change(self, widget):
		self.syntaxes[0][0].color=(255,255-self.priority * 10,255-self.priority * 10,255)
		#brightness decreases as priority increases..such are the paradoxes of our lives..


class Idea(Note):
	def __init__(self, text=""):
		super(Idea,self).__init__()
	
		self.syntaxes = [[t("idea: "), w("text")]]
		self.text = widgets.Text(self, text)


class Clock(Node):
	def __init__(self):
		super(Clock,self).__init__()
		self.datetime = __import__("datetime")
	def render(self):
		return [t(str(self.datetime.datetime.now()))]

	def eval(self):
		self.runtime.evaluated = True
		self.runtime.value.append(Value(self.get_value()))
		return self.runtime.value.val
		

class Assignment(Syntaxed):
	syntaxes=[[ch("left"), t(" = "), ch("right")],
			[t("set "), ch("left"), t(" to "), ch("right")],
			[t("let "), ch("left"), t(" be "), ch("right")]]

	def __init__(self):
		self.child_types = {'left': [Typeref(b[SomethingNew]), Typeref(b[VariableReference]), Typeref(b[ArrayIndexation])],
			'right': [b['expression']]}
		super(Assignment,self).__init__()
		

	@staticmethod
	def make_proto():
		return Assignment(Placeholder(['somethingnew', 'variablereference']),NodeCollider(['variablereference', 'expression']))

	#def eval(self):
	#see the_doc
	#	if isinstance(self.left, SomethingNew):
	#		self.runtime.value = 


class Subclass(Syntaxed):
	syntaxes=[[ch("left"), t("is a subclass of"), ch("right")]]
	def __init__(self):
		self.child_types = {'left': [b['somethingnew']], 'right':[b['subclass'], b['builtintypedecl']]}
		super(Subclass,self).__init__()
		#assert(right.__class__.tolower() in works_as('type'))

	@staticmethod
	def make(left, right):
		assert(isinstance(left, (NodeCollider, SomethingNew)))
		r = Subclass()
		r.setch('left', left)
		r.setch('right', right)
		return r

class IsLessThan(Syntaxed):
	syntaxes=[[ch("left"), t(" < "), ch("right")]]
	def __init__(self):
		super(IsLessThan,self).__init__()
		self.child_types = {'left': b[Number], 'right': b[Number]}

	def eval():
		l,r = self.ch.left.eval(), self.ch.right.eval()
		assert(isinstance(l, Value))
		assert(isinstance(r, Value))
		return self.runtime.value.append(Value(l < r))


class TypedArgument(Syntaxed):
	syntaxes=[[ch("name"), t(" - "), ch("type")]]
	def __init__(self):
		super(TypedArgument, self).__init__()
		self.child_types = {
			'name': [b['somethingnew']],
			'type': [b['type']]}


class FunctionSignature(Syntaxed):
	syntaxes = [[ch("sig")]]
	def __init__(self, sig):
		super(FunctionSignature, self).__init__()
		assert(isinstance(sig, (Collider, ListVal)))
		self.child_types = {'sig': [b['function signature list']]}



class FunctionDefinition(Syntaxed):
	syntaxes = [[t("function definition:"), ch("signature"), t(":\n"), ch("body")]]
	def __init__(self):
		super(FunctionDefinition, self).__init__()
		self.child_types = {'signature': b[FunctionSignature],
							'body': b[Statements]}


class While(Syntaxed):
	syntaxes = [[t("while"), ch("condition"), t("do:"), nl(), ch("statements")],
			 [t("repeat if"), ch("condition"), t("is true:"), nl(), ch("statements"), t("go back up..")]]
	def __init__(self):
		super(While, self).__init__()
		self.child_types = {
			'condition': WithParams(b["expression"], {"returning": b["bool"]}),
			'statements': b['Statements']}

class WithParams():
	def __init__(self, type, params):
		self.type = type
		self.params = params

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


ad = ArgumentDefinition
tv = TextVal

class BuiltinFunctionDecl(Syntaxed):
	def __init__(self, signature, eval):
		super(BuiltinFunctionDecl, self).__init__()
		self.setch('signature', FunctionSignature(signature))
		self.eval = eval
  		self.syntaxes = [[t("builtin function:"), ch("signature"), t(":"+str(eval))]]

"""
class PythonFunctionDecl(Syntaxed):
	def __init__(self, fun, sig, arg):
		self.setch('signature', FunctionSignature(sig))
		

PythonFunctionDecl(
	operator.div,
	signature = [ad("left"), tl("/"), ad("right")],
	arg_types = {'left': b['expression'], 'right': b['expression']})
"""



class FunctionCall(Node):
	def __init__(self, target):
		super(FunctionCall, self).__init__()
		assert isinstance(target, FunctionDefinition)
		self.target = target
		self.args = []
		for v in self.target.arg_types:
			x = NodeCollider()
			x.parent = self
			self.args.append(x)

	def replace_child(self, child, new):
		x = self.args.find(child)
		self.args[x] = new
		new.parent = self

	def render(self):
		r = [t('(call)')]
		for i in self.target.signature.items:
			if isinstance(i, TextLit):
				r += [t(i.widget.text)]
			elif isinstance(i, ArgumentDefinition):
				r += [ElementTag(self.args[i.name])]

		return r
#todo: show and hide argument names. syntaxed?






b['somethingnew'] = BuiltinNodeDecl(SomethingNew)
b['statements'] = BuiltinNodeDecl(Statements)

b['builtintypedecl'] = BuiltinNodeDecl(BuiltinTypeDecl)
b['subclass'] = BuiltinNodeDecl(Subclass)

b['comparable'] = BuiltinTypeDecl("comparable")
b['text'] = BuiltinTypeDecl('text')
b['number'] = Subclass.make(SomethingNew('number'), TypeRef(b['comparable']))
b['bool'] = BuiltinTypeDecl('bool')


b['multiply'] = BuiltinFunctionDecl(
	FunctionSignatures body should be b['function signature list']..
	FunctionSignature.make(ListVal.make([
		TypedArgument.make(
			SomethingNew.make("left"),
			TypeRef(b['number'])),
		,TextVal("*"),
		TypedArgument.make(
			SomethingNew.make("right"),
			TypeRef(b['number'])),
		], [b['typedargument'], b['textval']]),
	multiply_eval)

def multiply_eval(args):
		l,r = args.left.eval(), args.right.eval()
		assert(isinstance(l, Value))
		assert(isinstance(r, Value))
		res = Value(b['number'], l.value * r.value)
		return res


b['expression'] = BuiltinTypeDecl('expression')
b['type'] = NodeClass('type')


Definition("function signature list", Type(b['list'], [b['typedargument'], b['text']]))





builtins = Module("builtins")
builtins.ch.statements.items = list(b)

builtins.ch.statements.items += [
	 WorksAs(b['islessthan'], b['expression'])
	,worksAs(b['builtintypedecl'], b['type'])
	,worksAs(b['subclass'], b['type'])



]











#just mocking up boolean properties here


class ObjectDeclaration(Syntaxed):
	"""just mocking stuff up"""
	def __init__(self, kids):
		super(ObjectDeclaration, self).__init__(kids)
	@classmethod
	def cls_palette(cls, scope):
		r = []
		for x in scope:
			x = x.compiled
			if x.decl == cls.decl:
				print x, x.decl, cls.decl
				r += [CompilerMenuItem(Ref(x))]
		return r

SyntaxedNodecl(ObjectDeclaration,
               [ch("name"), t("is an object")],
               {'name': Slot(b['text'])})

class BooleanPropretyDeclaration(Syntaxed):
	"""just mocking stuff up"""
	def __init__(self, kids):
		super(BooleanPropretyDeclaration, self).__init__(kids)
SyntaxedNodecl(BooleanPropretyDeclaration,
               [ch("object"), t("can be"), ch("p1"), t("or"), ch("p2")],
               {'object': b['objectdeclaration'],
                'p1': Slot(b['text']),
				'p2': Slot(b['text'])})

class BooleanProperty(Node):
	def __init__(self, value):
		super(BooleanProperty, self).__init__()
		self.value = value
	def render(self):
		return [t(self.value)]

class BooleanPropertyNodecl(NodeclBase):
	def __init__(self):
		super(BooleanPropertyNodecl, self).__init__(Ref)
		b['booleanproperty'] = self
		BooleanProperty.decl = self
	def palette(self, scope):
		r = []
		decls = [x for x in scope if isinstance(x, (BooleanPropretyDeclaration))]
		for d in decls:
			r += [CompilerMenuItem(BooleanProperty(x.pyval)) for x in [d.ch.p1, d.ch.p2]]
		return r

BooleanPropertyNodecl()

class BooleanPropretyAssignment(Syntaxed):
	def __init__(self, kids):
		super(BooleanPropretyAssignment, self).__init__(kids)
SyntaxedNodecl(BooleanPropretyAssignment,
               [ch("object"), t("is"), ch("property")],
               {'object': b['objectdeclaration'],
                'property': b['booleanproperty']})










#end of mocking up boolean properties, serious stuff ahead
