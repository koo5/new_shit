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
from utils import assis

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
		charadd(lines[-1], " ", squash(atts))

def charadd(line, char, atts):
	a = squash(atts)
	assert(isinstance(a, dict))
	line.append((char, a))

def attadd(atts, tup):
	assis(atts, list)
	assis(tup, tuple)
	assis(tup[0], str)
	assert(len(tup) == 2)
	atts.append(("color", tag.color))

def project(root):
	lines = [[]]
	atts = []
	indent = 0
	_project(lines,root,atts,indent)
	return lines

#⇾node⇽
def _project(lines, elem, atts, indent):
	assis(elem, asselement.Element)
	tags = elem.tags()
	assert(isinstance(tags, list))
	assert(isinstance(lines, list))
	assert(isinstance(atts, list))
	assert(isinstance(indent, int))
	
	attadd(atts, "node", node)
	pos = -1 # <>
	
	for tag in [ColorTag((200,0,0)), TextTag("<"), EndTag()] + nt + [ColorTag((200,0,0)), TextTag(">"), EndTag()]:

		if isinstance(tag, NewlineTag):
			tag = TextTag("\n")

		if isinstance(tag, AttTag):
			attadd(atts, tag.key, tag.val)
		elif isinstance(tag, ColorTag):
			attadd(atts, "color", tag.color)

		elif isinstance(tag, ChildTag):
			ch = node.__getattr__(tag.name)
			_project(lines, ch, atts, indent)
		elif isinstance(tag, WidgetTag):
			w = node.__dict__[tag.name]
			_project(lines, w, atts, indent)	

		elif isinstance(tag, EndTag):
			atts.pop()

		elif isinstance(tag, IndentTag):
			indent+=1
		elif isinstance(tag, DedentTag):
			indent-=1

		elif isinstance(tag, BackspaceTag):
			if len(lines[-1]) < tag.spaces:
				log("cant backspace that much")
			lines[-1] = lines[-1][:-tag.spaces]

		elif isinstance(tag, TextTag):
			for char in tag.text:
				if char == "\n":
					newline(lines, indent, atts)
				else:
					attadd("char_index", pos)
					if len(lines[-1]) >= _width:
						newline(lines, indent, atts)
					
					tup = (char, squash(atts))
					
					assert(isinstance(tup[0], str))
					assert(isinstance(tup[1], dict))
					
					charadd(lines[-1], tup)
					
					atts.pop() #char_index
					pos += 1
		else:
			raise Hell
	return lines

def find(node, lines):
	assert(isinstance(node, asselements.Element))
	for r,line in enumerate(lines):
		for c,char in enumerate(line):
			if char[1]['node'] == node:
				return c, r
	return None


test_tags = [
		NodeTag(1),
		TextTag("program Hello World:\n"),
		IndentTag(),
		NodeTag(2),
		TextTag("print "),
		NodeTag(3),
		TextTag("\"hello world\"\n"),
		EndTag(),
		EndTag(),
		DedentTag(),
		TextTag("end."),
		EndTag()
	]

if __debug__:
	test_squash()

