from collections import OrderedDict
import pygame



from logger import ping, log
import element
import widgets
from menu import MenuItem, InfoMenuItem
import tags
from tags import ChildTag as ch, WidgetTag as w, TextTag as t, NewlineTag as nl, IndentTag as indent, DedentTag as dedent, ColorTag, EndTag, ElementTag, MenuTag
import project





#fuzzywuzzy , to help make sense of the error messages brought about by the __getattr__ madness
#would work without fuzzywuzzy, but its a nice training, this module will later be handy anyway

try:
	import fuzzywuzzy #pip install --user fuzzyfuzzy
	from fuzzywuzzy import process as fuzzywuzzyprocess
except:
	fuzzywuzzyprocess = None

class NotEvenAChildOrWidgetOrMaybePropretyGetterRaisedAnAttributeError(AttributeError):
	def __init__(self, wanted, obj):
		self.obj = obj
		self.wanted = wanted
	def __str__(self):
		r = "\"%s\" is not an attribute or child of %s, or maybe property getter raised AtributteError, if the name is found below, it did (or maybe you called __getitem__ directly, or confused ch() with w()):\n" % (self.wanted, self.obj)
		if fuzzywuzzyprocess:
			r += "attributes, widgets: " + ", ".join([i for i,v in fuzzywuzzyprocess.extractBests(self.wanted, dir(self.obj), limit=10, score_cutoff=50)]) + "...\n"
			assert(isinstance(self.obj, Node))
			r += "children: " + ", ".join([i for i,v in fuzzywuzzyprocess.extractBests(self.wanted, [x for x in self.obj.children], limit=10, score_cutoff=50)]) + "..."
		return r






#homebrew Xpath, for finding elements of the tree...what do?
#how it relates to the __getattr__ madness is unknown as of yet


def find_by_path(item, path):
	l = path.split("/")
	for i, x in enumerate(l):
		if x.isdigit():
			l[i] = int(x)
		elif "=" in x:
			spl = x.split("=")
			l[i] = {spl[0]:spl[1]}
		#else its a string.
	r = find_in(item, l)
	#log(r)
	return r

def find_in(item, path):
	#ping()
	assert(isinstance(item, (list, dict, element.Element)))
	i = tryget(item,path[0])
	if i == None:
		log("not found: " + str(path[0]) + " in " + str(item) + " / " + " / ".join([str(x) for x in path]))
		if isinstance(path[0], int):
			log("out of range?")
	if len(path) == 1 or i == None:
		return i #thats it! lets go home!
	else:
		return find_in(i, path[1:]) #recurse

def tryget(x,y):
	assert(isinstance(y, (str, int, dict)))
	try:
		
		if isinstance(y, dict):
			k,v = dict.iteritems()[0]
			for item in x.items:
				if k in dir(item):
					if v == getattr(item, k):
						return item
		
		else:
			return getattr(x, y)
	except:
		try:
			return x[y]
		except:
			return None
			




#a node is more than an element, it keeps track of its children with a dict.
#in the editor, nodes can be cut'n'pasted around on their own, which wouldnt
#make sense for widgets
#everything is lumped together here, real ast nodes with clock and sticky notes,
#tho some nodes broke away into toolbar.py settings.py menu.py and the_doc.py

class Node(element.Element):
	def __init__(self):
		super(Node, self).__init__()
		self.color = (0,255,0,255)
		self.children = {}

	def fix_relations(self):
		self.fix_(self.children)

	def __getattr__(self, name):
#		assert('children' in dir(self))
		#log(self)
		if self.children.has_key(name):
			return self.children[name]
		else:
			#raise AttributeError()
			raise NotEvenAChildOrWidgetOrMaybePropretyGetterRaisedAnAttributeError(name, self)

	def setch(self, key, item):
		self.children[key] = item
		item.parent = self
	

	def find(self, path):
		return find_by_path(self, path)

	def replace_child(self, child, new):
		ping()
		print self.children
		assert(child in self.children.values())
		for k,v in self.children.iteritems():
			if v == child:
				self.children[k] = new
		new.parent = self

	
#	def program(self):
#		if isinstance(self, Program):
#			return self
#		else:
#			if self.parent != None:
#				return self.parent.program()
#			else:
#				print self, "has no parent"
#				return None


"""
	def render_syntax(self, syntax):
		r = []
		for item in syntax:
			if isinstance(item, ch):
				if not self.children.has_key(item.name):
					log('expanding child "'+item.name+'" of node '+str(self))
					log("doesnt look good")
				r += self.children[item.name].tags()
			if isinstance(item, w):
				if not self.__dict__.has_key(item.name):
					log('expanding widget "'+item.name+'" of node '+str(self))		
					log("doesnt look good")
				r += self.__dict__[item.name].tags()
			else:
				r.append(item)
		return r
"""

class Syntaxed(Node):
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
			if e.key == pygame.K_PAGEDOWN:
				self.next_syntax()
				log("next")




class Text(Node):
	"""string literal"""
	def __init__(self, value):
		super(Text, self).__init__()
		self.widget = widgets.Text(self, value)
	def render(self):
		return [w('widget')]

class Number(Node):
	"""number literal"""
	def __init__(self, value):
		super(Number, self).__init__()
		self.widget = widgets.Number(self, value)
	def render(self):
		return [w('widget')]

#bool



class Collapsible(Node):
	"""Collapsible - List or Dict - dont have a title, a top unindented line. They are just
	the items...now"""
	def __init__(self, items, expanded=True):
		super(Collapsible, self).__init__()
		self.items = items #do this first or bad things will happen (and i forgot why)
		self.expand_collapse_button = widgets.Button(self)
		self.expand_collapse_button.push_handlers(on_click=self.on_widget_click)
		self.expanded = expanded
	
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
	def __init__(self, tuples, expanded=True):
		super(Dict, self).__init__(OrderedDict(tuples), expanded)
		#Dict is created from a list of pairs ("key", value)

		for key, item in self.items.iteritems():
			item.parent = self

	def render_items(self):
		r = []
		for key, item in self.items.iteritems():
			r += [t(key), t(":"), indent(), nl()]
			r += [ElementTag(item)]
			r += [dedent(), nl()]
		
		return r
#	def __getattr__(self, name):
#		if self.items.has_key(name):
#			return self.items[name]
#		else:
#			return super(Dict, self).__dict__[name]?
	def __getitem__(self, i):
		return self.items[i]

	def fix_relations(self):
		super(Dict, self).fix_relations()
		self.fix_(self.items)


class List(Collapsible):
	def __init__(self, items, expanded=True):
		super(List, self).__init__(items, expanded)
		assert(isinstance(items, list))
		for item in self.items:
			item.parent = self

	def render_items(self):
		r = []
		for item in self.items:
			r += [ElementTag(item)]# + [nl()]
		return r
	def __getitem__(self, i):
#		ping()
		return self.items[i]

	def replace_child(self, child, new):
		ping()
		assert(child in self.items)
		self.items[self.items.index(child)] = new
		new.parent = self

class CollapsibleText(Collapsible):
	def __init__(self, value):
		super(CollapsibleText, self).__init__(value)
		self.widget = widgets.Text(self, value)
	def render_items(self):
		return [w('widget')]
		

class Statements(List):
	pass	



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
		return [t(self.declaration.name.text)]


class SomethingNew(Node):
	def __init__(self, text):
		super(SomethingNew, self).__init__()
		self.text = text
	def render(self):
		return [t("?"),t(self.text), t("?")]




class Placeholder(Node):
	def __init__(self, types=None, description = "write here"):
		super(Placeholder, self).__init__()
		self.types = types
		self.description = description
		self.textbox = widgets.ShadowedText(self, "", self.description)
		self.brackets_color = (0,255,0)
		self.textbox.brackets_color = (255,255,0)


	def render(self):
		return [w('textbox')]


	#to be moved to node
	def scope(self):
		x = self.root.find("modules/1/statements/items")
		assert(x != None)
		return x

	
	def menu(self):
		text = self.textbox.text
		r = [InfoMenuItem("insert:")]
		it = PlaceholderMenuItem

		if text.isdigit():
			r += [it(Number(text))]

		r += [it(Text(text))]

		r += [it(SomethingNew(text))]

		#variables, functions
		for i in self.scope():
			if isinstance(i, VariableDeclaration):
				r += [it(VariableReference(i))]
			if isinstance(i, FunctionDefinition):
				r += [it(FunctionCall(i))]

		#1: node types
		#r += [it(x) for x in self.scope()]

#		r += [it(Program(Statements([Placeholder()])))] #fix SyntaxDef
		r += [it(Module(Statements([Placeholder()])))]
		
		r += [it(While(Placeholder([], "condition"), 
						Statements([Placeholder([], "statement")])))]
		
		r += [it(Note(text)), it(Todo(text)), it(Idea(text))]
				
		#2: calls, variables..
		
		#filter by self.types:
		
		#preferred types:
		#r += expand_types(self.types)
		#all types
		#r += expand_types('all') - expand_types(self.types)

		return r	
			

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
					menu.bg)
				s.blit(sur,(chx,chy))
				area = area.union((chx, chy, sur.get_rect().w, sur.get_rect().h+2))
		return area


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
	def __init__(self, syntax_def):
		super(WithDef, self).__init__()
		self.syntax_def = syntax_def
		
	def render(self):
		return self.syntax_def.syntax_def

class Program(WithDef):
	def __init__(self, statements, name="unnamed", author="banana", date_created="1.1.1.1111"):
		super(Program, self).__init__(syntax_def = "fix")
		
		assert isinstance(statements, Statements)
		self.sys=__import__("sys")

		self.setch('statements', statements)
		self.setch('name', widgets.Text(self, name))
		self.setch('author', widgets.Text(self, author))
		self.setch('date_created', widgets.Text(self, date_created))
			

class Module(Syntaxed):
	def __init__(self, statements, name="unnamed"):
		super(Module, self).__init__()
		assert isinstance(statements, Statements)
		self.setch('statements', statements)
		self.name = widgets.Text(self, name)
		self.syntaxes = [[t("module"), w("name"), nl(), ch("statements"), t("end.")]]
		

class FunctionDefinition(Syntaxed):
	def __init__(self, syntax, body):
		super(FunctionDefinition, self).__init__()
		assert isinstance(body, Statements)
		assert isinstance(syntax, SyntaxDef)
		self.setch('body', body)
		self.setch('syntax', syntax)
		self.syntaxes = [[t("function definition:"), ch("syntax"), t("body:"), ch("body")]]

class FunctionCall(Syntaxed):
	def __init__(self, definition):
		super(FunctionCall, self).__init__()
		assert isinstance(definition, FunctionDefinition)
		self.definition = definition
		self.syntaxes = [[t("call"), w("definition")]]

class ShellCommand(Syntaxed):
	def __init__(self, command):
		super(ShellCommand, self).__init__()
		self.command = widgets.Text(self, command)
		self.syntaxes = [[t("run shell command:"), w("command")]]

class Root(Syntaxed):
	def __init__(self, items):
		super(Root, self).__init__()
		self.parent = None
		self.post_render_move_caret = 0
		self._indent_length = 4
		self.setch('items', items)
		self.syntaxes = [
			[ColorTag((255,255,255,255)), ch("items"), EndTag()],
			[ColorTag((255,255,255,255)), t("root of all evil:"), nl(), ch("items"), EndTag()]
			]

	def find(self, path):
		return find_by_path(self.items.items, path)

	@property
	def indent_length(self):
		return self._indent_length

class While(Syntaxed):
	def __init__(self,condition,statements):
		super(While,self).__init__()

		self.syntaxes = [[t("while"), ch("condition"), t("do:"), nl(), ch("statements")],
						 [t("repeat if"), ch("condition"), t("is true:"), nl(), ch("statements"), t("go back up..")]]
		self.setch('condition', condition)
		self.setch('statements', statements)

	#def new():
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

"""
could start working on:

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





outdated stuff and comments here:

class Asignment(Templated):
	def __init__(self, left, right):
		super(Asignment,self).__init__()
		self.templates=[template([child("left"), t(" = "), child("right")]),
				template([t("set "), child("left"), t(" to "), child("right")]),
				template([t("have "), child("left"), t(" be "), child("right")])]
		self.set('left', left)
		self.set('right', right)
		
class IsLessThan(Templated):
	def __init__(self, left, right):
		super(IsLessThan,self).__init__()

		self.templates=[template([child("left"), t(" < "), child("right")])]
		self.set('left', left)
		self.set('right', right)
		

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
"""	


