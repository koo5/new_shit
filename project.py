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
from dotdict import dotdict

if __debug__:
	import element as asselement
	import typed as assnodes



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


def newline(p, elem):
	elem._render_lines[-1]["end"] = len(p.lines[-1])

	p.lines.append([])
	for i in range(p.indent * p.indent_width):
		#keeps the attributes of the last node,
		#but lets see how this works in the ui..
		charadd(p.lines[-1], " ", p.atts)

	elem._render_lines.append({
		"start": len(p.lines[-1]),
		"line": len(p.lines)-1})


def charadd(line, char, atts):
	assert(isinstance(atts, list))
	a = squash(atts)
	assert(isinstance(a, dict))
	line.append((char, a))

def attadd(atts, key, val):
	assert(isinstance(key, str))
	atts.append((key, val))

def new_p(cols):
	p = dotdict()
	p.width = cols
	p.indent_width = 4
	p.atts = []
	p.lines = [[]]
	p.arrows = []
	p.indent = 0
	return p

def project(root, cols):
	p = new_p(cols)
	_project_elem(p, root)
	return p

def project_tags(tags, cols):
	p = new_p(cols)
	p._render_lines = [{}]
	_project_tags(p, p, tags, 0)
	return p

def _project_elem(p, elem):
	assert(isinstance(elem, asselement.Element))
	assert(isinstance(p.lines, list))
	assert(isinstance(p.atts, list))
	assert(isinstance(p.indent, int))

	elem._render_lines = [
		{"start": len(p.lines[-1]),
		 "line": len(p.lines)-1}]

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

	_project_tags(p, elem, tags, pos)

def _project_tags(p, elem, tags, pos):

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
			tag = ElementTag(elem.__dict__[tag.name]) #get widget #?

	#now real stuff
		if isinstance(tag, str):
			for char in tag:
				attadd(p.atts, "char_index", pos)
				if char == "\n":
					newline(p, elem)
				else:
					if len(p.lines[-1]) >= p.width:
						newline(p, elem)
					charadd(p.lines[-1], char, p.atts)
				p.atts.pop()
				pos += 1

		#recurse
		elif isinstance(tag, ElementTag):
			_project_elem(p, tag.element)

		#attributes
		elif isinstance(tag, EndTag):
			p.atts.pop()

		elif isinstance(tag, AttTag):
			attadd(p.atts, tag.key, tag.val)
		elif isinstance(tag, ColorTag):
			attadd(p.atts, "color", tag.color)

		elif isinstance(tag, ArrowTag):
			p.arrows.append((len(p.lines[-1]), len(p.lines) - 1, tag.target))

		elif isinstance(tag, IndentTag):
			p.indent+=1
		elif isinstance(tag, DedentTag):
			p.indent-=1
		#elif isinstance(tag, BackspaceTag):
		#	if len(lines[-1]) < tag.spaces:
		#		log("cant backspace that much")
		#	lines[-1] = lines[-1][:-tag.spaces]
		#elif isinstance(tag, MenuTag):
		#	screen['menu'] = tag
		else:
			raise Exception("is %s a tag?" % tag)

	elem._render_lines[-1]["end"] = len(p.lines[-1]) - 1



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
