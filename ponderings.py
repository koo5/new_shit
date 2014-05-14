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

class BaseNode(Node):
	syntax = [t("god created a base class for all nodes")]

b['node'] = BaseNode()

class Subclass(Node):
	def __init__(self, name, superclass):
		self.name = name
		self.superclass = superclass

def add_to_builtins(node):
	b[node.name.value] = node

add_to_builtins(node) for node in [
	Subclass(Text('while'), b['statement'])

Subclass('expression', b['statement'])
Attrib(b['expression'], 'evaluates to')
#expression has an attribute "evaluates to"

Subclass('literal', b['expression'])
class Literal(Syntaxed):
	attributes = {"evaluates to":

Subclass('number', b['literal'])
#number is a subclass of expression
#"evaluates to" of number is number

ImplementedBy(b['number'], Number)




Subclass(Text("declaration"), b['node']))
Subclass(Text('subclass'), b['declaration'])
ImplementedBy(b['subclass'], Subclass)



every node object must have X.attribs


