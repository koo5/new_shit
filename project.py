# -*- coding: utf-8 -*-


"""
functon project takes a list of tags created by root.tags()
 and outputs a list of lines
 line is a list of tuples: (character, attributes)

 break line on "\n"
 later: break too long lines
"""

from tags import *
from logger import ping, log


if __debug__:
	import element as asselement
	import nodes as assnodes


_width = 5 #screen width
_indent_width = 4


def squash(l):
#	ping()
	assert(isinstance(l, list))
	for i in l:
		assert(isinstance(i, tuple))
		assert(len(i) == 2)
		assert(isinstance(i[0], str))
		
	r = {}
	for i in l:
		r[i[0]] = i[1]
	return r


def test_squash():
	if squash([("a", 1), ("b", 2), ("a", 3)]) != {"a": 3, "b": 2}:
		raise Exception()

def newline(lines, indent, atts):
	lines.append([])
	for i in range(indent * _indent_width):
		#keeps the attributes of the last node,
		#but lets see how this works in the ui..
		charadd(lines[-1], " ", atts)

def charadd(line, char, atts):
	assert(isinstance(atts, list))
	a = squash(atts)
	assert(isinstance(a, dict))
	line.append((char, a))

def attadd(atts, key, val):
	assert(isinstance(key, str))
	atts.append((key, val))

def project(root):
	screen = {'lines': [[]]}
	atts = []
	indent = 0
	_project(screen,root,atts,indent)
	return screen

#⇾node⇽
def _project(screen, elem, atts, indent):
	"""calls elem.tags(), then calls itself recursively on widget,
	child and element tags.	screen and atts are passed and mutated"""
	
	assert(isinstance(elem, asselement.Element))
	assert(isinstance(screen, dict))

	lines = screen['lines']
	tags = elem.tags()

	assert(isinstance(tags, list))
	assert(isinstance(lines, list))
	assert(isinstance(atts, list))
	assert(isinstance(indent, int))
	
	attadd(atts, "node", elem)
	pos = -1 # <>
	
	for tag in [ColorTag((200,0,0)), TextTag("<"), EndTag()] + tags + [ColorTag((200,0,0)), TextTag(">"), EndTag()]:

	#first some replaces
		if isinstance(tag, NewlineTag):
			tag = TextTag("\n")

		elif isinstance(tag, ChildTag):
			assert(isinstance(elem, assnodes.Node))
			tag = ElementTag(elem.__getattr__(tag.name)) #get child
		elif isinstance(tag, WidgetTag):
			tag = ElementTag(elem.__dict__[tag.name]) #get widget

	#now real stuff

		if isinstance(tag, AttTag):
			attadd(atts, tag.key, tag.val)
		elif isinstance(tag, ColorTag):
			attadd(atts, "color", tag.color)

		elif isinstance(tag, ElementTag):
			_project(screen, tag.element, atts, indent)

		elif isinstance(tag, EndTag):
			atts.pop()

		elif isinstance(tag, IndentTag):
			indent+=1
		elif isinstance(tag, DedentTag):
			indent-=1
		#elif isinstance(tag, BackspaceTag):
		#	if len(lines[-1]) < tag.spaces:
		#		log("cant backspace that much")
		#	lines[-1] = lines[-1][:-tag.spaces]
		elif isinstance(tag, TextTag):
			for char in tag.text:
				attadd(atts, "char_index", pos)
				if char == "\n":
					newline(lines, indent, atts)
				else:
					if len(lines[-1]) >= _width:
						newline(lines, indent, atts)
					charadd(lines[-1], char, atts)
				atts.pop()
				pos += 1
				
		elif isinstance(tag, MenuTag):
			screen['menu'] = tag
		else:
			raise Hell


def find(node, lines):
	assert(isinstance(node, asselement.Element))
	for r,line in enumerate(lines):
		for c,char in enumerate(line):
			if char[1]['node'] == node:
				return c, r
	return None


if __debug__:
	test_squash()

