from collections import OrderedDict



import element
import widgets
import tags
from tags import ch, t, nl, indent, dedent


#class triple


class Node(element.Element):
	def __init__(self):
		super(Node, self).__init__()
		self.color = (0,255,0,255)

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
	

class Syntaxed(Node):
	def __init__(self):
		super(Syntaxed, self).__init__()
		self.syntax_index = 0
	@property
	def syntax(self):
		return self.syntaxes[self.syntax_index]
	def render(self):
		res = []
		for item in self.syntax:
			if isinstance(item, child):
				res += self.children[item.name].tags()
			else
				res += item
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
		self.widget = widgets.Text(value)
	def render(self):
		self.widget.render()

class Number(Node):
	def __init__(self, value):
		super(Number, self).__init__()
		self.widget = widgets.Number(value)
	def render(self):
		self.widget.render()





class Collapsible(Node):
	def __init__(self, items):
		super(Collapsible, self).__init__()
		self.items = items #do this first or bad things will happen (?)
		self.set('expand_collapse_button', widgets.Button())
		self.expand_collapse_button.push_handlers(on_click=self.on_widget_click)
		self.expanded = True
	def render(self):
		self.expand_collapse_button.text = (
			("-" if self.expanded else "+") +
			(" " * (self.win.indent_length - 1)))
		return self.expand_collapse_button.tags() + 
			indent() + 
			(self.render_items() if self.expanded else newline()) +
			dedent()
	
	def toggle(self):
		self.expanded = not self.expanded

	def on_widget_click(self, widget):
		if widget is self.expand_collapse_button:
			self.toggle()

class Dict(Collapsible):
	def __init__(self, *tuples):
		super(Dict, self).__init__(OrderedDict(tuples))
		for key, item in self.items.iteritems():
			item.parent = self

	def render_items(self):
			for key, item in self.items.iteritems():
				self.doc.append(key+":", self)
				if hasattr(item, "oneliner"):
					self.doc.append(" ", self)
				else:
					self.doc.append("\n", self)
				item.render()
				self.doc.newline(item)
	def __getattr__(self, name):
		if self.items.has_key(name):
			return self.items[name]
		else:
			return super(Dict, self).__getattr__(name)

class List(Collapsible):
	def __init__(self, items):
		super(List, self).__init__(items)
		assert(isinstance(items, list))
		for item in self.items:
			item.parent = self

	def render_items(self):
			for item in self.items:
				item.render()
				self.doc.newline(item)
	def __getitem__(self, i):
		if len(self.items) > i:
			return self.items[i]
		else:
			return super(List, self).__getitem__(i) #?


class CollapsibleText(Collapsible):
	def __init__(self, value):
		super(CollapsibleText, self).__init__(value)
		self.set('widget', widgets.Text(value))
	def render_items(self):
		self.widget.render()
		

class Statements(List):
	pass	

class VariableRead(Node):
	def __init__(self, name):
		super(VariableRead, self).__init__()
		self.name = widgets.Text(name)
	def render(self):
		self.name.render()

class Placeholder(Node):
	def __init__(self, name="placeholder", type=None, default="None", example="None"):
		super(Placeholder, self).__init__()
		self.default = default
		self.example = example
		self.set('textbox', widgets.ShadowedText("", "<<>>"))
		self.set('menu', widgets.Menu([]))
		self.textbox.push_handlers(
			on_edit=self.on_widget_edit,
			on_text=self.on_widget_text,
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

		x = d + e if self.doc.active == self.textbox else ""


		self.textbox.shadow = "<<" + x + ">>"

		self.textbox.render()
#		print self.menu.items
		self.menu.render()


	def on_widget_text(self, text):
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
		self.doc.append(str(self.datetime.datetime.now()), self)





class Program(Templated):
	def __init__(self, statements, name="unnamed", author="banana", date_created="1.1.1.1111"):
		super(Program, self).__init__()
		assert isinstance(statements, Statements)
		self.sys=__import__("sys")
		self.templates = [template([t("program by "), child("author"),s(), t("created on "), child("date_created"), newline(), child("statements"), t("end.")]),
						template([t("lemon operating language running on python"), t(self.sys.version.replace("\n", "")), t(" ready."), newline(),child("statements")])]
		self.set('statements', statements)
		self.set('author', widgets.Text(author))
		self.set('date_created', widgets.Text(date_created))

#	@property
#	def uses(self):
#		for i in self.statements.items:
			

class Templates(List):
	def __init__(self,items):
		super(Templates,self).__init__()


class While(Templated):
	def __init__(self,condition,statements):
		super(While,self).__init__()

		self.templates = [template([t("while "), child("condition"), t(" do:"),newline(),child("statements")]),
		template([t("repeat if "), child("condition"), t(" is true:"),newline(),child("statements"),t("go back up..")])]
		self.set('condition', condition)
		self.set('statements', statements)


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

"""
#set backlight brightness to %{number}%
self.templates = target.call_templates?
class CallNode(TemplatedNode):
	def __init__(self, target=):
		super(CallNode,self).__init__()
		self.target = target
		self.arguments = arguments
	def render(self):
		self.target
"""		
		
class Note(Node):
	def __init__(self):
		super(Note,self).__init__()
	
class Todo(Note):
	def __init__(self, text="", priority = 1):
		super(Todo,self).__init__()
		self.priority_widget = widgets.Number
		if priority == 10:
			self.color=(255,0,0,255)
		self.syntaxes = [[t("todo:"), ch("text")]]
		self.set('text', widgets.Text(text))
class Idea(Useless):
	def __init__(self, text=""):
		super(Idea,self).__init__()
	
		self.templates = [template([t("idea: "), child("text")])]
		self.set('text', widgets.Text(text))

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

test_progra_syntax = SyntaxNode([





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
