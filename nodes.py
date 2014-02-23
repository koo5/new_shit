from collections import OrderedDict


from logger import ping, log
import element
import widgets
import menu
import tags
from tags import ChildTag as ch, WidgetTag as w, TextTag as t, NewlineTag as nl, IndentTag as indent, DedentTag as dedent



try:
	import fuzzywuzzy #pip install --user fuzzyfuzzy
	from fuzzywuzzy import process as fuzzywuzzyprocess
except:
	fuzzywuzzyprocess = None

class NotEvenAChildOrWidgetError(AttributeError):
	def __init__(self, wanted, obj):
		self.obj = obj
		self.wanted = wanted
	def __str__(self):
		r = "\"%s\" is not an attribute or child of %s" % (self.wanted, self.obj)
		if fuzzywuzzyprocess:
			r += ", you might have meant: " + ", ".join([i for i,v in fuzzywuzzyprocess.extractBests(self.wanted, dir(self.obj), limit=10, score_cutoff=50)]) + "..."
		return r


class Node(element.Element):
	def __init__(self):
		super(Node, self).__init__()
		self.color = (0,255,0,255)
		self.children = {}

	def fix_relations(self):
		self.fix_(self.children)

	def setch(self, key, item):
		self.children[key] = item
		item.parent = self

	def __getattr__(self, name):
		if self.children.has_key(name):
			return self.children[name]
		else:
			#raise AttributeError()
			raise NotEvenAChildOrWidgetError(name, self)


#	def program(self):
#		if isinstance(self, Program):
#			return self
#		else:
#			if self.parent != None:
#				return self.parent.program()
#			else:
#				print self, "has no parent"
#				return None


	def scope(self):
		pass


	def render_syntax(self, syntax):
		r = []
		for item in syntax:
			if isinstance(item, ch):
				log('expanding child "'+item.name+'" of node '+str(self))
				if not self.children.has_key(item.name):
					log("doesnt look good")
				r += self.children[item.name].tags()
			if isinstance(item, w):
				log('expanding widget "'+item.name+'" of node '+str(self))
				if not self.__dict__.has_key(item.name):
					log("doesnt look good")
				r += self.__dict__[item.name].tags()
			else:
				r.append(item)
		return r


class Syntaxed(Node):
	def __init__(self):
		super(Syntaxed, self).__init__()
		self.syntax_index = 0
	@property
	def syntax(self):
		return self.syntaxes[self.syntax_index]
	def render(self):
		return self.render_syntax(self.syntax)
	def prev_syntax(self):
		self.syntax_index  -= 1
		if self.syntax_index < 0:
			self.syntax_index = 0
	def next_syntax(self):
		self.syntax_index  += 1
		if self.syntax_index == len(self.syntaxes):
			self.syntax_index = len(self.syntaxes)-1
	def on_key_press(self, key, modifiers):
		if (pyglet.window.key.MOD_CTRL & modifiers) and (key == pyglet.window.key.UP):
			self.prev_syntax()
			log("prev")
		if (pyglet.window.key.MOD_CTRL & modifiers) and (key == pyglet.window.key.DOWN):
			self.next_syntax()
			log("next")


#literals

class Text(Node):
	def __init__(self, value):
		super(Text, self).__init__()
		self.widget = widgets.Text(self, value)
	def render(self):
		return self.widget.tags()

class Number(Node):
	def __init__(self, value):
		super(Number, self).__init__()
		self.widget = widgets.Number(self, value)
	def render(self):
		return self.widget.tags()





class Collapsible(Node):
	def __init__(self, items):
		super(Collapsible, self).__init__()
		self.items = items #do this first or bad things will happen (and i forgot why)
		self.expand_collapse_button = widgets.Button(self)
		self.expand_collapse_button.push_handlers(on_click=self.on_widget_click)
		self.expanded = True
	
	def render(self):
		self.expand_collapse_button.text = (
			("-" if self.expanded else "+") +
			(" " * (self.win.indent_length - 1)))
		return self.expand_collapse_button.tags() + [indent()] + (self.render_items() if self.expanded else [newline()]) + [dedent()]
	
	def toggle(self):
		self.expanded = not self.expanded

	def on_widget_click(self, widget):
		if widget is self.expand_collapse_button:
			self.toggle()

class Dict(Collapsible):
	def __init__(self, tuples):
		super(Dict, self).__init__(OrderedDict(tuples))
		#Dict is created from a list of pairs ("key", value)

		for key, item in self.items.iteritems():
			item.parent = self

	def render_items(self):
		r = []
		for key, item in self.items.iteritems():
			r.append(t(key+":"))
			r += item.tags()
			r.append(nl())
		return r
#	def __getattr__(self, name):
#		if self.items.has_key(name):
#			return self.items[name]
#		else:
#			return super(Dict, self).__dict__[name]?
	def __getitem__(self, i):
		return self.items[i]


class List(Collapsible):
	def __init__(self, items):
		super(List, self).__init__(items)
		assert(isinstance(items, list))
		for item in self.items:
			item.parent = self

	def render_items(self):
		r = []
		for item in self.items:
			r += item.tags()# + [nl()]
		return r
	def __getitem__(self, i):
		return self.items[i]


class CollapsibleText(Collapsible):
	def __init__(self, value):
		super(CollapsibleText, self).__init__(value)
		self.widget = widgets.Text(self, value)
	def render_items(self):
		return self.widget.tags()
		

class Statements(List):
	pass	

class VariableRead(Node):
	def __init__(self, name):
		super(VariableRead, self).__init__()
		self.name = widgets.Text(name)
	def render(self):
		return self.name.tags()

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

		return self.textbox.tags() + self.menu.tags()


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
	
	

class Clock(Node):
	def __init__(self):
		super(Node,self).__init__()
		self.datetime = __import__("datetime")
	def render(self):
		return [t(str(self.datetime.datetime.now()))]

#design:
#the difference between Syntaxed and WithDef is that Syntaxed
#has the syntaxes as part of "class definition" (in __init__, really)
#WithDef uses another object, "SyntaxDef"

class SyntaxDef(Syntaxed):
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
		return self.render_syntax(self.syntax_def.syntax_def)

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
		

class FunctionDefNode(Syntaxed):
	def __init__(self, syntax, body):
		super(FunctionDefNode, self).__init__()
		assert isinstance(body, Statements)
		self.setch('body', body)
		self.setch('syntax', SyntaxDef(syntax))
		self.syntaxes = [[t("function definition:"), ch("syntax"), t("body:"), ch("body")]]


class ShellCommand(Syntaxed):
	def __init__(self, command):
		super(ShellCommand, self).__init__()
		self.command = widgets.Text(self, command)
		self.syntaxes = [[t("run shell command:"), w("command")]]

class Root(Syntaxed):
	def __init__(self, items):
		super(Root, self).__init__()
		self.setch('items', items)
		self.syntaxes = [[t("root of all evil:"), nl(), ch("items")]]
	

class While(Syntaxed):
	def __init__(self,condition,statements):
		super(While,self).__init__()

		self.syntaxes = [[t("while"), ch("condition"), t("do:"), nl(), ch("statements")],
						 [t("repeat if"), ch("condition"), t("is true:"), nl(), ch("statements"), t("go back up..")]]
		self.setch('condition', condition)
		self.setch('statements', statements)


class Note(Syntaxed):
	def __init__(self, text=""):
		super(Note,self).__init__()
		self.syntaxes = [[t("note: "), w("text")]]
		self.text = widgets.Text(self, text)

class Todo(Note):
	def __init__(self, text="", priority = 1):
		super(Todo,self).__init__(text)
		self.syntaxes = [[t("todo:"), w("text"), w("priority_widget")]]
		self.text = widgets.Text(self, text)
		self.priority_widget = widgets.Number(self, priority)
		self.priority_widget.push_handlers(
			on_change=self.on_priority_change)
		self.on_priority_change("whatever")

	@property
	def priority(self):
		return self.priority_widget.value

	def on_priority_change(self, widget):
		self.color=(255,255-self.priority * 10,255-self.priority * 10,255)
		#total brightness decreases as priority increases..such are the paradoxes of our lives

class Idea(Note):
	def __init__(self, text=""):
		super(Idea,self).__init__()
	
		self.syntaxes = [[t("idea: "), w("text")]]
		self.text = widgets.Text(self, text)



"""

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

#class triple
"""
