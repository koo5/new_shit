# -*- coding: utf-8 -*-


"""
functon project takes a list of tags created by root.tags()
 and outputs a list of lines
 line is a list of tuples: (character, attributes)
 break line on "\n".
"""

from tags import *
from logger import ping, log
import colors
from typed import Node

if __debug__:
	import element as asselement
	import typed as assnodes


_indent_width = 4


def squash(l):
#	ping()
	if __debug__:
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
	assert squash([("a", 1), ("b", 2), ("a", 3)]) == {"a": 3, "b": 2}


def newline(lines, indent, atts, elem):
	elem._render_lines[-1]["end"] = len(lines[-1])

	lines.append([])
	for i in range(indent * _indent_width):
		#keeps the attributes of the last node,
		#but lets see how this works in the ui..
		charadd(lines[-1], " ", atts)

	elem._render_lines.append({
		"start": len(lines[-1]),
		"line": len(lines)})


def charadd(line, char, atts):
	assert(isinstance(atts, list))
	a = squash(atts)
	assert(isinstance(a, dict))
	line.append((char, a))

def attadd(atts, key, val):
	assert(isinstance(key, str))
	atts.append((key, val))

def project(root, width):
	global _width
	_width = width

	atts = []
	indent = 0
	lines = [[]]
	_project(lines,root,atts,indent)
	return lines

def _project(lines, elem, atts, indent):
	"""calls elem.tags(), then calls itself recursively on widget,
	child and element tags.	lines and atts are passed and mutated"""
	assert(isinstance(elem, (asselement.Element, assnodes.CompilerMenuItem)))
	print elem
	assert(isinstance(lines, list))
	assert(isinstance(atts, list))
	assert(isinstance(indent, int))

	elem._render_lines = [
		{"start": len(lines[-1]),
		 "line": len(lines)}]

	tags = [AttTag("node", elem)]

	pos = -1 # because of the "<"
	tags += [ColorTag(elem.brackets_color), TextTag(elem.brackets[0]), EndTag()]
	tags += elem.tags()
	tags += [ColorTag(elem.brackets_color), TextTag(elem.brackets[1]), EndTag()]

	#results of eval
	if isinstance(elem, Node):
		if elem.runtime.has_key("value") and elem.runtime.has_key("evaluated"):
			"""
			if elem.runtime.has_key("unimplemented"):
				text = "unimplemented"
			else:
				text = ', '.join([str(x) for x in elem.runtime.value])
			"""
			tags += [ColorTag((155,155,155)), TextTag(":")]
			tags += [ElementTag(elem.runtime.value.val)]
			tags += [TextTag(" "), EndTag()]



	tags += [EndTag()]

	for tag in tags:
	#first some replaces
		if isinstance(tag, NewlineTag):
			tag = "\n"
		elif isinstance(tag, TextTag):
			tag = tag.text

		elif isinstance(tag, ChildTag):
			assert(isinstance(elem, assnodes.Node))
			assert(isinstance(elem.ch[tag.name], asselement.Element))
			tag = ElementTag(elem.ch[tag.name]) #get child
		elif isinstance(tag, WidgetTag):
			tag = ElementTag(elem.__dict__[tag.name]) #get widget

	#now real stuff
		if isinstance(tag, str):
			for char in tag:
				attadd(atts, "char_index", pos)
				if char == "\n":
					newline(lines, indent, atts, elem)
				else:
					if len(lines[-1]) >= _width:
						newline(lines, indent, atts, elem)
					charadd(lines[-1], char, atts)
				atts.pop()
				pos += 1

		#recurse
		elif isinstance(tag, ElementTag):
			_project(lines, tag.element, atts, indent)

		#attributes
		elif isinstance(tag, EndTag):
			atts.pop()

		elif isinstance(tag, AttTag):
			attadd(atts, tag.key, tag.val)
		elif isinstance(tag, ColorTag):
			attadd(atts, "color", colors.modify(tag.color))

		elif isinstance(tag, ArrowTag):
			attadd(atts, "arrow", tag.target)

		elif isinstance(tag, IndentTag):
			indent+=1
		elif isinstance(tag, DedentTag):
			indent-=1
		#elif isinstance(tag, BackspaceTag):
		#	if len(lines[-1]) < tag.spaces:
		#		log("cant backspace that much")
		#	lines[-1] = lines[-1][:-tag.spaces]
		#elif isinstance(tag, MenuTag):
		#	screen['menu'] = tag
		else:
			raise Exception("is %s a tag?" % tag)

	elem._render_lines[-1]["end"] = len(lines[-1])


def find(node, lines):
	assert(isinstance(node, asselement.Element))
	for r,line in enumerate(lines):
		for c,char in enumerate(line):
			if char[1]['node'] == node:
				return c, r
	return None


if __debug__:
	test_squash()

#⇾node⇽
