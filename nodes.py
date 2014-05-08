#beware misleading documentation


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
from logger import ping, log
import element
import widgets
from menu import MenuItem, InfoMenuItem, HelpMenuItem
import tags
from tags import ChildTag as ch, WidgetTag as w, TextTag as t, NewlineTag as nl, IndentTag as indent, DedentTag as dedent, ColorTag, EndTag, ElementTag, MenuTag
import project
import colors




b = {}




class TypeRef(Node):
	def __init__(self, target):
		self.target = target
		assert(isinstance(target, (BuiltinTypeDef, Subclass)))










class val(list):
	"""
	a list of Values
	during execution, results of evaluation of every node is appended, so there is a history visible, and the current value is the last one"""
	def val(self):
		return self[-1]

	def append(self, x):
		assert(isinstance(x, Value))
		super(self, val).append(x)
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
	def __init__(self):
		super(Syntaxed, self).__init__()
		self.syntax_index = 0
		for name, types in self.child_types.iteritems():
			if len(types) == 1 and types[0].equals(TypeRef(b[Statements])):
			
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
			if v[0] == 'statements':
				x = Statements()
			else:
				 x = NodeCollider(v)
			r.children[k] = x







class BuiltinNodeDecl(Node):
	def __init__(self, decl):
		super(BuiltinNodeDecl, self).__init__()
		self.decl = decl

	def render(self):
		return [t("builtin node declaration:"), t(str(self.decl))]





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

b['text'] = BuiltinTypeDecl('text')
class TextVal(WidgetedValue):
	def __init__(self, value):
		super(TextVal, self).__init__()
		self.type = TypeRef(b['text'])
		self.widget = widgets.Text(self, "")

b['number'] = BuiltinTypeDecl('number')
class NumberVal(WidgetedValue):
	def __init__(self, value):
		super(NumberVal, self).__init__()
		self.type = TypeRef(b['number'])
		self.widget = widgets.Number(self, 0)

b['bool'] = BuiltinTypeDecl('bool')
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

class Statements(List):
	def __init__(self):
		List.__init__(self, types=['statement'], expanded=True, vertical=True)

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



class SomethingNew(Node):
	def __init__(self, text):
		super(SomethingNew, self).__init__()
		self.text = text
	def render(self):
		return [t("?"),t(self.text), t("?")]










class Module(Syntaxed):
	syntaxes = [[t("module"), w("name"), nl(), ch("statements"), t("end.")]]
	child_types = {'statements': 'statements'}

	def __init__(self, name="unnamed"):
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
	child_types = {
					'statements': 'statements',
					'name': ['text'],
					'author': ['text']}

	def __init__(self):
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

class While(Syntaxed):
	def __init__(self):
		super(While,self).__init__()

		self.syntaxes = [[t("while"), ch("condition"), t("do:"), nl(), ch("statements")],
						 [t("repeat if"), ch("condition"), t("is true:"), nl(), ch("statements"), t("go back up..")]]
		self.setch('condition',
			NodeCollider(["expression"]))
		self.setch('statements',Statements())

	def eval(self):
		self.runtime.evaluated = True	

	#def now():#prototype
	#	return While(Placeholder(),Statements([Placeholder()]))

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
			'right': b['expression']}
		super(Assignment,self).__init__()
		

	@staticmethod
	def make_proto():
		return Assignment(Placeholder(['somethingnew', 'variablereference']),NodeCollider(['variablereference', 'expression']))

	#def eval(self):
	#see the_doc
	#	if isinstance(self.left, SomethingNew):
	#		self.runtime.value = 


class Subclass(Syntaxed):
	def __init__(self, left, right):
		super(TypeDeclaration,self).__init__()
		assert(isinstance(left, SomethingNew))
		#assert(right.__class__.tolower() in works_as('type'))
		self.syntaxes=[[ch("left"), t("is a kind of"), ch("right")]]
		self.setch('left', left)
		self.setch('right', right)

class TypeRef(Node):
	def __init__(self, target):
		super(TypeRef, self).__init__()
		assert(isinstance(target, (BuiltinTypeDeclaration, Subclass)))
		self.target = target
		
	def render(self):
		return self.target.name.text

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


class ArgumentDefinition(Syntaxed):
	syntaxes=[[ch("name"), t(" - "), ch("type")]]
	def __init__(self):
		super(ArgumentDefinition, self).__init__()
		self.child_types = {'name', b['text'], 'type', b['type literal']}


class FunctionSignature(Syntaxed):
	syntaxes = [[ch("args")]]
	def __init__(self):
		super(self, FunctionSignature).__init__()
		self.child_types = {'items': Typeref(b[ListVal])}


class FunctionDefinition(Syntaxed):
	self.syntaxes = [[t("function definition:"), ch("signature"), t(":\n"), ch("body")]]
	def __init__(self):
		super(FunctionDefinition, self).__init__()
		self.child_types = {'signature': Typeref(b[FunctionSignature]),
							'body': Typeref(b[Statements])}


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



b['comparable'] = BuiltinTypeDecl(name = "comparable")
b['number'] = Subclass(name = 'number', (b['comparable']))


ad = ArgumentDefinition
tl = TextLit

class BuiltinFunctionDecl(Syntaxed):
	def __init__(self, name, signature, arg_types,):
		super(BuiltinFunctionDecl, self).__init__()
		self.setch('signature', FunctionSignature(signature))
		self.arg_types = arg_types
		self.eval = eval
		self.name = name
		self.syntaxes = [[t("builtin function:"), ch("signature"), t(":"+str(eval))]]

b['multiply'] = BuiltinFunctionDecl(
	name = 'multiply',
	signature = [ad("left"), tl("*"), ad("right")],
	arg_types = {'left': b['expression'], 'right': b['expression']},
	eval = multiply_eval)

def multiply_eval(args):
		l,r = args.left.eval(), args.right.eval()
		assert(isinstance(l, Value))
		assert(isinstance(r, Value))
		res = Value(b['number'], l.value * r.value)
		return res

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




"""	
type declarations:
	definitions:
		banana is a kind of fruit
	builtin:
		Dict

type reference

x is a dict of fruits

class hashmap
	declaration syntax: a hashmap from [x - type] to [y - type]

	x is a hashmap from int to string


variable declaration:
	ch("name"), t("is a(n)"), ch("type")
	child_types = {"name": Text, "type": b['type']}
	
class BuiltinType(Node):
	works_as = b['type']
	def __init__(self, type):
		self.type = type

b['number'] = BuiltinType(Number, [[t("number")]])
b['list'] =  BuiltinType(List, [[t("list of"), ch("items type")]], {"items type": b['type']})
b['function'] = BuiltinType


class EnumType
name
list of values
indexation type

ListType
ListLiteral
ListValue?

class FunctionType(Syntaxed):
	syntaxes = [[t("function taking"), ch("args"), t("and returning"), ch("result")]]
	def __init__(
		self.child_types = {'args': [XofYs(b[Dict], b[ArgumentDefinition])]}
		super(self, FunctionType).__init__()

types are literals
wherever you point to python class, point to builtin declaration instead

oR JUST vithout types:

class VariableDeclaration(Node):
	def __init__(self, name):
		super(VariableDeclaration, self).__init__()
		self.name = widgets.Text(name)
	def render(self):
		return [t("var"), w('name')]

class VariableReference(Node):
	def __init__(self, declaration):
		super(VariableReference, self).__init__()
		self.declaration = declaration
	def render(self):
		return [t("->"+self.declaration.name.text)]
`well-
"""


"""


for x in ['statement', 'typedeclaration', 'expression']:
	b[x] = TypeClass(x)

for x in [Text, Number, Bool, Dict, List, Statements, Assignment, Program, IsLessThan]:
	b[x] = b[x.__class__.__name__] = BuiltinType(x)

"""



"""
roadmap: 
types - try to figure out or leave for later
 pyswip integration
functions
logic
"""

"""
tbd:
class Terminal(Syntaxed):
	def __init__(self):
		self.setch('history', List([]))
		self.setch('command', Placeholder())
		self.run_button = widgets.Button(self, "run")
		self.syntaxes = [[t("history:"), ch('history'), t('command'), ch('command'), w('run_button')]

	def on_keypress(self, e):
		if pygame.KMOD_CTRL & e.mod:
			if e.key == pygame.K_RETURN:
				self.history.append(self.command.eval()...
			
"""


"""

class CustomNode(Syntaxed):
	syntaxes = [[ch("syntaxes"), ch("works as"), ch("name")]]
	def __init__(self):
		super(CustomNode, self).__init__()
		self.child_types = {'name', b['text'], 
			'works as', b['type']}

CustomNode(
	ch = {'syntaxes':[[ch("name"), t(" - "), ch("type")]]
	def __init__(self):
		super(ArgumentDefinition, self).__init__()
		self.child_types = {'name', b['text'], 'type', b['type']}




"""




"""
for x in [Statements, Clock, Program, Module, Note, Todo, Idea,
			ArgumentDefinition, TextLit]:
	b[x] = BuiltinNodeDecl(x)
				
"""


"""
outdated:
class Triple(Syntaxed):
	def __init__(self, subject, predicate, object):
		super(Triple, self).__init__()
		self.setch('subject', subject)
		self.setch('predicate', predicate)
		self.setch('object', object)
		self.syntaxes = [[ch("subject"), ch("predicate"), ch("object")]]
	@staticmethod
	def make_proto():
		return Triple(Placeholder(['term', 'somethingnew']),Placeholder(['term', 'somethingnew']),Placeholder(['term', 'somethingnew'])),



class Print(Templated):
	def __init__(self,value):
		super(Print,self).__init__()
	
		self.templates = [template([t("print "), child("value")]),
				template([t("say "), child("value")])]
		self.set('value', value)


#set backlight brightness to %{number}%
self.templates = target.call_templates?

class If(Templated):
	def __init__(self,condition,statements):
		super(If,self).__init__()

		self.templates = [template([t("if "), child("condition"), t(" then:"),newline(),child("statements")])]
		self.set('condition', condition)
		self.set('statements', statements)
	
	def step(self):
		if self.condition.step():
			self.statements.step()
		

class Array(Templated):
	def __init__(self,item, items):
		super(Array,self).__init__()

		self.templates = [template([t("["), child("items"),t("]")])]
		self.set('items', items)
		
class ArrayItems(Node):
	def __init__(self,items):
		super(ArrayItems,self).__init__()

	def render(self):
		for i,item in enumerate(self.items):
			self.doc.append(str(item), self)
			if i != len(self.items):
				self.doc.append(", ", self)

"""

"""
musings:			

#start adding a knowledge base
#brick is a kind of thing
#brick 1 is a brick
#brick1 is blue
#every blue brick


#child, parent -> sub, sup?
#CarryNode?:)


#class SillySimpleCommandDeclaration()


class Grid(Node):
	def __init__(self, items, grid):
		super(Grid,self).__init__()
		self.items = items
		self.grid = grid
		
	def render(self):
		return [TwoDGraphicTag(self)]


wolframalpha
	input text
	get back results

tap into eulergui datagui functionality (DBpedia)

class SemanticizedGoogle
	nah, huge and stupid

snatch ubuntu scopes




"""	

"""
old stuff:
pyDatalog.create_terms('link, can_reach, X, Y, Z, Number, Text, CollapsibleText')
+link(Number, Text)
+link(Text, CollapsibleText)
link(X,Y) <= link(Y,X)


# can Y be reached from X ?
can_reach(X,Y) <= link(X,Y) # direct link
# via Z
can_reach(X,Y) <= link(X,Z) & can_reach(Z,Y) & (X!=Y)


print (can_reach(Number,Y))


#pyDatalog.create_terms('works_as')
#works_as(Assignment, 'assignment')
#sum([])


works_as(Number, 'expression')
+works_as(Bool, 'bool')
+works_as(Equals, 'bool')
+works_as('expression', 'statement')
+works_as(X, Y): works_as(X, Z) and works_as(Z, Y)
+would_work_as(
+---------------------------------------------------------
+Assignment, assignment
+assignment, statement
+Number number
+Bool bool
+number expression
+bool expression
+Equality bool
+would_work_as(number, bool)?
+would_work_as(X, Y):-
+       would_work_as(Z, Y),
+       in_syntax(Z,X).
+
+       would_work_as(
+works_as('expression', 'statement')
+works_as(X, Y): works_as(X, Z) and works_as(Z, Y)


"""


"""

def make_protos(root, text):
	r = {'module': Module(),
		'while': While(),
		'bool': Bool(False),
		'text': Text(text),
		'number': Number(text),
		'note': Note(text),
		'todo': Todo(text),
		'idea': Idea(text),
		'assignment': Assignment.make_proto(),
		'program': Program(),
		'islessthan': IsLessThan(),
		'typedeclaration': TypeDeclaration(SomethingNew(text), SomethingNew("?")),
		'functiondefinition': FunctionDefinition(),
		'argumentdefinition': ArgumentDefinition(),
		'triple': Triple.make_proto()
		}


	return r



"""





"""NodeCollider and Placeholder..megamess atm. should allow adding both node classes
and expressions with matching types.
collider has a list of nodes and should allow adding and deleting.
back to dummy? collider is responsible for menu?
its probably reasonable to forego all smartness for a start and do just a dumb
tree editor
"""


class NodeCollider(Node):
	def __init__(self, types):
		super(NodeCollider, self).__init__()
		self.types = types
		self.items = []
		self.add(Placeholder(types))

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

	def menu(self):
		r = [InfoMenuItem("magic goes here")]

		for type in self.types:
			r += [InfoMenuItem("for type "+type)]
			for w in works_as(type):
				r += [InfoMenuItem(w + "works as "+type)]
				if nodes_by_name.has_key(w):
					n = nodes_by_name[w]()
					#todo: use NodeTypeDeclarations instead
					if isinstance(n, Syntaxed):
						for syntax in n.syntaxes:
							for i in range(min(len(self.items), len(syntax))):
								if isinstance(syntax[i], tags.TextTag):
									if isinstance(self.items[i], SomethingNew):
										r += [InfoMenuItem(str(w))]


		r += [InfoMenuItem("banana")]
		return r

	def replace_child(self, child, new):
		assert(child in self.items)
		self.items[self.items.index(child)] = new
		new.parent = self
		p = Placeholder(self.types)
		p.parent = self
		self.items.append(p)

	def eval(self):
		i = self.items[0]
		i.eval()
		self.runtime = i.runtime
		return self.runtime.value.val


class Placeholder(Node):
	def __init__(self, types, description = None):
		super(Placeholder, self).__init__()
		self.types = types
		if description == None: description = str(types)
		self.description = description
		self.textbox = widgets.ShadowedText(self, "", self.description)
		self.brackets_color = (0,255,0)
		self.textbox.brackets_color = (255,255,0)

	def render(self):
		return [w('textbox')]
	
	def menu(self):
		text = self.textbox.text
		#r = [InfoMenuItem("insert:")]
		it = PlaceholderMenuItem

		r = []

		if text.isdigit():
			r += [it(Number(text))]

		#r += [it(Text(text))]
		r += [it(SomethingNew(text))]

		protos = make_protos(self.root, text)
		#for k,v in protos.iteritems():
		#	v.parent = self
		
		#first the preferred types
		for t in self.types:
			for v in works_as(t):
				if protos.has_key(v):
					x = protos[v]
					menuitem = it(x)
					r += [menuitem]
					
					if isinstance(x, Syntaxed):
						for s in x.syntaxes:
							#print s
							tag = s[0]
							if isinstance(tag, tags.TextTag):
								if text in tag.text:
									menuitem.score += 1
									#print x
									#if not protos[v] in [i.value for i in r]:
										
				elif v == 'functioncall':
					for i in self.scope():
						if isinstance(i, FunctionDefinition):
							r += [it(FunctionCall(i))]
				
				elif v == 'termreference':
					for i in self.scope():
						if isinstance(i, Triple):
							r += [it(i.subject)]
							r += [it(i.object)]
				
				elif v == 'dbpediaterm':
							r += [it(x) for x in DbpediaTerm.enumerate()]

				elif v == 'variablereference':
					print "scope:", self.scope()


		#then add the rest
		#for t in self.types:
		#	for v in works_as(t):
		#		if protos.has_key(v) and not protos[v] in [i.value for i in r]:
		#			r += [it(protos[v])]

		#enumerators:
		#	scope:
		#		variables, functions
		#			
	
		"""
		if type == 'pythonidentifier'
			PythonIdentifier.enumerate(self)

		if type == 'google'
			Google.enumerate(self)
		
		"""
	

		#variables, functions
#		for i in self.scope():
#			if isinstance(i, VariableDeclaration):
#				r += [it(VariableReference(i))]
#			if isinstance(i, FunctionDefinition):
#				r += [it(FunctionCall(i))]

		#1: node types
		#r += [it(x) for x in self.scope()]

#add best
#add all

				
		#2: calls, variables..
		
		#filter by self.types:
		
		#preferred types:
		#r += expand_types(self.types)
		#all types
		#r += expand_types('all') - expand_types(self.types)

		#sort:
		
		#r.sort(key = self.fits)

		return super(Placeholder, self).menu() + r
		
		
	def fits(self, item):
		for t in self.types:
			if isinstance(item, t):
				return 1
		return 0
		

	def menu_item_selected(self, item):
		if not isinstance(item, PlaceholderMenuItem):
			log("not PlaceholderMenuItem")
			return
		v = item.value
		if v == None:
			log("no value")
		elif isinstance(v, NodeTypeDeclaration):
			x = v.type()
		elif isinstance(v, Node):
			x = v
#		elif isinstance(v, type):
#			x = v()
		self.parent.replace_child(self, x)

# hack here, to make a menu item renderable by project.project
class PlaceholderMenuItem(MenuItem):
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
















builtins = Module("builtins")
builtins.ch.statements.items = list(b)
