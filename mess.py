__author__ = 'kook'


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
		self.add(SomethingNew())

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


