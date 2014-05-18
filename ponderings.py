i think the question is, should syntaxes be defined from the point of view
of the editor: "for body you can place a block of statements, for condition
a node returning bool, for arguments a list of ArgumentDefinitions"

or the point of view of runtime: for condition a bool, for  



i managed to properly word it later: the question is wether the type system shold be defined from the point of view of the language/runtime or from the pov of the editor/syntax.
The syntax pov it makes more sense. So where there was condition: Bool, there will now be condition: expression returning bool.

so im now focusing on parametric types. parametric nodes, actually?

the basic idea: TypeDeclaration defines parameters.
for example, ListType has "item type". instances of type objects then fill them with values.

but to do "expression returning Bool", practically every node in the language must derive from Expression

		
	
		
		

class BaseNode(Syntaxed):
	syntax = [t("god created a base class for all nodes")]

b['node'] = BaseNode()

class Subclass(Node):
	def __init__(self, name, superclass):
		if isinstance(name, str):
			name = Text(name)
		self.name = name
		self.superclass = superclass

IsSubclass('statement', b['node'])
IsSubclass('while', b['statement'])
IsSubclass('expression', b['statement'])
HasAttrib(b['expression'], 'evaluates to')
Subclass('literal', b['expression'])

class Literal(Syntaxed):
	_attribs = {"evaluates to":.

Subclass('number', b['literal'])
#number is a subclass of expression
#"evaluates to" of number is number

ImplementedBy(b['number'], Number)










Subclass(Text("declaration"), b['node']))
Subclass(Text('subclass'), b['declaration'])
ImplementedBy(b['subclass'], Subclass)








every node object must have X.attribs








def add_to_builtins(node):
	b[node.name.value] = node
add_to_builtins(node) for node in [

def bi(l):
	for i in l:
		b[i.name] = i







class FriendBackupEngine(Syntaxed):
	syntaxes = [[
friend backup engine:
	"Music" is shared with rszeno
	rszeno is "identities/rszeno.foaf.rdf"






while
if
variable declaration
variable reference
assignment





	



class Type(Node):
	__init__(self):
		self.child_types = {'attrib names': TypeRef(b['list']),
				'attrib values': b['node'],
				'supertype': b['node']} 
	instantiate(self):

bi(Type('list', (



TypeRef('list' ['of'], 


FunctionType(

condition: Type(b['node'], {'evaluating to': b['bool']})


Define("siglist", Type(b['list'], {'of':Type(b['union'], {



backup_machine = node()
backup_machine.child_types = {"body": 






Type3('node', None)
Type3('list', b['node'], ['of'])
Definition('function signature list', TypeRef(b['list'], {'of': b['union







class TypeRef(Syntaxed):
	def __init__(self, target, attribs):
		self.target = target
		self.attribs = attribs

class Type3(Syntaxed):
	def __init__(self, name, supertype, ):
		self.name = name
		self.supertype = supertype
		
	



b['number'] = {'instances_evaluate_to': b['number'],
		





Type('statements', b['node']


























class TypeRef(Syntaxed):
	syntaxes = [[ch("target"), ch("attribs")]]
	def __init__(self, target, attribs):

		self.target = target
		self.attribs = attribs

	def child_types():
		return {"target": [b['number'], ...]}...
		
		
		
		
		
		
		
		
class ListType(Syntaxed):
	syntaxes = [[t("list of"), ch("itemtype")]]
	def __init__(self, children):
		super(self, ListType).__init__(children)
		self.child_types = {'itemtype': b['type']}
			
		


class TypeRef(Syntaxed):
	def __init__(self, target, attribs):
		self.target = target
	
class WidgetedValue(Node):
	def __init__(self):
		super(WidgetedValue, self).__init__()	
	def pyval(self):
		return self.widget.value
	def render(self):
		return [w('widget')]

class NumberType(Node):9
	__init__(self):
		self.name = 'number'
		self.evaluates_to = self
		self.python_class = Number
	

b['number'] = NumberType()


class NumberVal(WidgetedValue):
	def __init__(self, value):
		super(NumberVal, self).__init__()
		self.type = TypeRef(b['number'])
		self.widget = widgets.Number(self, 555)




class SomethingNewType(Node):
	__init__(self):
		self.name = 'something new'
		self.evaluates_to = self
		self.python_class = SomethingNew
	
mode = eval/pass/node

VariableDecl:
	{'name': b['text'],
	 'type': b['type']}


b['type'] = TypeType()

class TypeType(
	name = 'type'
	
for each declaration in scope
	if declaration.isinstanceof(
















<function returning <int>>
a is a <list of <ints>>





