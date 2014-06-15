import sys
sys.path.append("/home/kook/pyDatalog-0.14.5")
from pyDatalog import pyDatalog
class Node(pyDatalog.Mixin):
	banana = True
class Text(Node):
	def __init__(self):
		super(self, Text).__init__()
class Number(Node):
	def __init__(self):
		super(self, Number).__init__()
class Type(Node):
	def __init__(self):
		super(self, Type).__init__()
def node(X):
	return isinstance(X, Node)
pyDatalog.create_terms('node, works_as, works_ass, node_works_as, X, Y, Z')
works_as(Number, Type)
works_as(Text, Type)
works_ass(X, Y) <= works_as(X, Y)
works_ass(X, Y) <= works_as(X, Z) & works_ass(Z, Y)
node_works_as(X, Y) <= works_ass(X, Y) & node(X)
node_works_as(X, X) <= node(X)

#can_reach(X,Y) <= link(X,Z) & can_reach(Z,Y) & (X!=Y)

print (node_works_as(X, 'type'))


#pyDatalog.create_terms('works_as')
#works_as(Assignment, 'assignment')
#sum([])


"""


node(variablereference).
node(typedeclaration).
node(typereference).
node(argumentdefinition).
node(functionsignature).
node(functiondefinition).
node(functioncall).
node(while).
node(note).
node(todo).
node(idea).
node(assignment).
node(module).
node(bool).
node(number).
node(text).
node(program).
node(islessthan).

works_as(islessthan, expression).
works_as(variablereference, expression).
works_as(type, statement).
works_as(functiondefinition, statement).
works_as(functioncall, expression).
works_as(text, expression).
works_as(number, expression).
works_as(bool, expression).
works_as(expression, statement).
works_as(while, statement).
works_as(note, statement).
works_as(todo, statement).
works_as(idea, statement).
works_as(assignment, statement).
works_as(statement, all).
works_as(module, all).
"""

"""
statement --> [if].
statement --> expression.
expression --> [bool].
expression --> [number].
expression --> [comparison].


if_syntax --> "if", [bool], "then", statement_syntax
comparison_syntax --> expression "==" expression

statement("if", [X, _])?
"""
