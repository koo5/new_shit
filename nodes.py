import pygame
from collections import OrderedDict
from compiler.ast import flatten




from dotdict import dotdict
from logger import ping, log
import element
import widgets
from menu import MenuItem, InfoMenuItem, HelpMenuItem
import tags
from tags import ChildTag as ch, WidgetTag as w, TextTag as t, NewlineTag as nl, IndentTag as indent, DedentTag as dedent, ColorTag, EndTag, ElementTag, MenuTag
import project
import colors




import pyswip
prolog = pyswip.Prolog()
prolog.consult("wat.pl")
pl_node_works_as = pyswip.Functor("node_works_as", 2)

def works_as(y):
	r = []
	X = pyswip.Variable()
	q = pyswip.Query(pl_node_works_as(X, y))
	while q.nextSolution():
		r += [str(X.value)]
	q.closeQuery()
	#print r
	return r




class val(list):
	def val(self):
		return self[-1]

class Value(object):
	def __init__(self, value):
		self.value = value




#a node is more than an element, it keeps track of its children with a dict.
#in the editor, nodes can be cut'n'pasted around on their own, which wouldnt
#make sense for widgets
#everything is lumped together here, real ast nodes with clock and sticky notes,
#tho some nodes broke away into toolbar.py settings.py and the_doc.py

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
		self.runtime.value.append(Value(None))
		self.runtime.evaluated = True
		self.runtime.implemented = False
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



class Literal(Node):
	def __init__(self):
		super(Literal, self).__init__()	
	def eval(self):
		v = Value(self.get_value())
		self.runtime.value.append(v)
		self.runtime.evaluated = True
		return v
	def get_value(self):
		return self.widget.text


class Text(Literal):
	def __init__(self, value):
		super(Text, self).__init__()
		self.widget = widgets.Text(self, value)
	def render(self):
		return [w('widget')]

class Number(Literal):
	def __init__(self, value):
		super(Number, self).__init__()
		self.widget = widgets.Number(self, value)
	def render(self):
		return [w('widget')]

class Bool(Literal):
	def __init__(self, value):
		super(Bool, self).__init__()
		self.widget = widgets.Toggle(self, value)
	def render(self):
		return [w('widget')]



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

	def __getattr__(self, name):
		if self.items.has_key(name):
			return self.items[name]
		else:
			raise AttributeError()

	def __getitem__(self, i):
		return self.items[i]

	def fix_parents(self):
		super(Dict, self).fix_relations()
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

	def fix_parents(self):
		super(List, self).fix_relations()
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

class CollapsibleText(Collapsible):
	def __init__(self, value):
		super(CollapsibleText, self).__init__(value)
		self.widget = widgets.Text(self, value)
	def render_items(self):
		return [w('widget')]
		

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


class NodeCollider(Node):
	def __init__(self, types=['all']):
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
				r += [InfoMenuItem("works as "+w)]
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
	def __init__(self, types=['all'], description = None):
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


class SomethingNew(Node):
	def __init__(self, text):
		super(SomethingNew, self).__init__()
		self.text = text
	def render(self):
		return [t("?"),t(self.text), t("?")]



#design:
#the difference between Syntaxed and WithDef is that Syntaxed
#has the syntaxes as part of "class definition" (in __init__, really)
#WithDef uses another object, "SyntaxDef"
class NodeTypeDeclaration(Node):
	def __init__(self, type):
		super(NodeTypeDeclaration, self).__init__()
		self.type = type

	def render(self):
		return [t("node type declaration:"), t(str(self.type))]


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




class Root(Dict):
	def __init__(self):
		super(Root, self).__init__()
		self.parent = None
		self.post_render_move_caret = 0
		self.indent_length = 4

	def render(self):
		return [ColorTag((255,255,255,255))] + self.render_items() + [EndTag()]






class Syntaxed(Node):
	child_types = {}

	def __init__(self):
		super(Syntaxed, self).__init__()
		self.syntax_index = 0

	@property
	def syntax(self):
		return self.syntaxes[self.syntax_index]

	def render(self):
#		return self.render_syntax(self.syntax)
		return self.syntax

	def prev_syntax(self):
		self.syntax_index  -= 1
		if self.syntax_index < 0:
			self.syntax_index = 0

	def next_syntax(self):
		self.syntax_index  += 1
		if self.syntax_index == len(self.syntaxes):
			self.syntax_index = len(self.syntaxes)-1

	def on_keypress(self, e):
		if pygame.KMOD_CTRL & e.mod:
			if e.key == pygame.K_PAGEUP:
				self.prev_syntax()
				log("prev")
				return True
			if e.key == pygame.K_PAGEDOWN:
				self.next_syntax()
				log("next")
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

class Module(Syntaxed):
	syntaxes = [[t("module"), w("name"), nl(), ch("statements"), t("end.")]]
	child_types = {'statements', 'statements'}

	def __init__(self, name="unnamed"):
		super(Module, self).__init__()
		self.name = widgets.Text(self, name)

	def add(self, item):
		self.statements.add(item)

#r['program'].syntax_def = root.find('modules/items/0/statements/items/0')
#assert(isinstance(r['program'].syntax_def, SyntaxDef))
class Program(Syntaxed):
	syntaxes = [[t("program by "), ch("author"), nl(), ch("statements"), t("end."), w("run_button"), w("results")]]
	child_types = {
					'statements': ['statements'],
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
	def __init__(self):
		super(Assignment,self).__init__()
		self.syntaxes=[[ch("left"), t(" = "), ch("right")],
					[t("set "), ch("left"), t(" to "), ch("right")],
					[t("have "), ch("left"), t(" be "), ch("right")]]
		self.setch('left', left)
		self.setch('right', right)

	@staticmethod
	def make_proto():
		return Assignment(Placeholder(['somethingnew', 'variablereference']),NodeCollider(['variablereference', 'expression']))

	#def eval(self):
	#see the_doc
	#	if isinstance(self.left, SomethingNew):
	#		self.runtime.value = 

class RootTypeDeclaration(Syntaxed):
	def __init__(self):
		super(RootTypeDeclaration, self).__init__()
		self.syntaxes=[[t("Values have types, every type derives from RootType.")]]


class TypeDeclaration(Syntaxed):
	def __init__(self, left, right):
		super(TypeDeclaration,self).__init__()
		assert(isinstance(left, SomethingNew))
		#assert(right.__class__.tolower() in works_as('type'))
		self.syntaxes=[[ch("left"), t("is a kind of"), ch("right")]]
		self.setch('left', left)
		self.setch('right', right)

class TypeReference(Node):
	def __init__(self, target):
		super(TypeReference, self).__init__()
		assert(isinstance(target, TypeDeclaration))
		self.target = target
		
	def render(self):
		return self.target.left.text


class NewStyle(Syntaxed):
	def __init__(self):
		super(NewStyle,self).__init__()
		self.types = {}
	
	def child(self, name, types):
		self.setch(name, Placeholder(types))
		self.types[name] = types

class IsLessThan(NewStyle):
	def __init__(self):
		super(IsLessThan,self).__init__()
		self.syntaxes=[[ch("left"), t(" < "), ch("right")]]
		self.child('left', ['number'])
		self.child('right', ['number'])

	def eval():
		l,r = self.left.eval(), self.right.eval()
		assert(isinstance(l, Value))
		assert(isinstance(r, Value))
		self.runtime.value.append(Value(l < r))


class ArgumentDefinition(NewStyle):
	def __init__(self):
		super(ArgumentDefinition, self).__init__()
		self.syntaxes=[[ch("name"), t(" - "), ch("type")]]
		self.child('name', ['text'])
		self.child('type', ['typereference'])


class FunctionSignature(NewStyle):
	def __init__(self):
		super(FunctionSignature, self).__init__()
		self.syntaxes=[[t("function:"),ch("items")]]
		self.setch('items', List(types=['argumentdefinition', 'text']))

#class PythonFunctionCall
#class LemonFunctionCall

class FunctionDefinition(Syntaxed):
	def __init__(self):
		super(FunctionDefinition, self).__init__()
		self.setch('body', Statements())
		self.setch('signature', FunctionSignature())
		self.syntaxes = [[t("function definition:"), ch("signature"), t(":\n"), ch("body")]]


class FunctionCall(Syntaxed):
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



"""
class PythonImport
	name

class pythonIdentifier


PythonFunctionDefinition(
class PythonFunctionDefinition(Syntaxed):
	def __init__(self, signature, body):
		super(FunctionDefinition, self).__init__()
		assert isinstance(body, Statements)
		assert isinstance(signature, FunctionSignature)
		self.setch('body', body)
		self.setch('signature', signature)
		self.syntaxes = [[t("function definition:"), ch("signature"), t(":\n"), ch("body")]]
"""

"""
		

class Print(Templated):
	def __init__(self,value):
		super(Print,self).__init__()
	
		self.templates = [template([t("print "), child("value")]),
				template([t("say "), child("value")])]
		self.set('value', value)


#set backlight brightness to %{number}%
self.templates = target.call_templates?
class CallNode(TemplatedNode):
	def __init__(self, target=):
		super(CallNode,self).__init__()
		self.target = target
		self.arguments = arguments
	def render(self):
		self.target


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
			
		
class FunctionDefinition(Templated):
	def __init__(self,signature,statements):
		super(FunctionDefinition,self).__init__()

		self.templates = [template([t("to "), child("signature"), t(":"),newline(),child("statements")])]
		self.set('signature', signature)
		self.set('statements', statements)

def FunctionArgument(Templated):
	def __init__(self,name,type):
		super(FunctionArgument,self).__init__()

		self.templates = [template([t("("),child("name"), t(" - "),child("type"),t(")"),])]
		self.set('name', name)
		self.set('type', type)

	

class FunctionSignature(Node):
	def __init__(self,items):
		super(FunctionSignature,self).__init__()
		self.items = items
	def render(self):
		for item in self.items:
			item.render()	

	

class SyntaxNode(Node):
	def __init__(self, items):
		self.items = items




#curent todo: add all nodes to the builtins module, with their templates:
#python classes are in nodes.py, with same names
#division?



#why not provide template functionality in Node: this is developing towards other views alla larch, maybe dataflow, maybe some other stuff, so using the inheritance hierarchy for all that will make more sense. I will try to declare a hierarchy inside the l1 declarations in modules


#start adding a knowledge base
#brick is a kind of thing
#brick 1 is a brick
#brick1 is blue
#every blue brick


#possible todo: ditch pyglets text modules for our own system:
#easier to make interaction glitch free
#non text representations: pyglets embedded objects or this
#is one format for one line enough, or do we need the full thing



#child, parent -> sub, sup?
#CarryNode?:)


#class SillySimpleCommandDeclaration()

"""


"""
class Placeholder(Node):
	def __init__(self, name="placeholder", type=None, default="None", example="None"):
		super(Placeholder, self).__init__()
		self.default = default
		self.example = example
		self.textbox = widgets.ShadowedText(self, "", "<<>>")
		self.menu = menu.Menu(self, [])
		self.textbox.push_handlers(
			on_edit=self.on_widget_edit
			#on_text_motion=self.on_widget_text_motion,
			)

#		print self," items:"
#		for name, item in self.__dict__.iteritems():
#			print " ",name, ": ", item
	
	
	def on_widget_edit(self, widget):
		if widget == self.textbox:
			text = self.textbox.text
			self.menu.items = self.doc.language.menu(self)
	
	def render(self):
		d = (" (default:"+self.default+")") if self.default else ""
		e = (" (for example:"+self.example+")") if self.example else ""

		x = d + e if self.textbox.is_active() else ""


		self.textbox.shadow = "<<" + x + ">>"

		return [w('textbox'), w('menu')]


	def on_widget_text_motion(self, motion):
		#use just shifts?
		if text == "T":
			self.menu.sel -= 1
			return True
		if text == "N":
			self.menu.sel += 1
			return True
			
	#def replace(self, replacement):
	#	parent.children[self.name] = replacement...


could start working on:

#not sure im gonna finish this one..it was supposed to be something like sticky notes,
#an alternative view of "notes"
#however, semanticizing or organizing into nodes all documentation is still a priority
class Grid(Node):
	def __init__(self, items, grid):
		super(Grid,self).__init__()
		self.items = items
		self.grid = grid
		
	def render(self):
		return [TwoDGraphicTag(self)]


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
			

	

class triple
	this would be three SomethingNew's - subject predicate object

wolframalpha
	input text
	get back results

or tap into eulergui datagui functionality

class SemanticizedGoogle
	nah, huge and stupid






"""	

"""
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


nodes_by_name = {
	'module': Module,
	'while': While,
	'bool': Bool,
	'text': Text,
	'number': Number,
	'note': Note,
	'todo': Todo,
	'idea': Idea,
    'assignment': Assignment,
	'program': Program,
	'islessthan': IsLessThan,
	'typedeclaration': TypeDeclaration,
	'functiondefinition': FunctionDefinition,
	'argumentdefinition': ArgumentDefinition,
    'functioncall': FunctionCall
}



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



