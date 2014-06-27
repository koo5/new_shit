# -*- coding: utf-8 -*-


"""
functon project takes a list of tags created by root.tags()
 and outputs a list of lines
 line is a list of tuples: (character, attributes)
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
#	if __debug__:
#		assert(isinstance(l, list))
#		for i in l:
#			assert(isinstance(i, tuple))
#			assert(len(i) == 2)
#			assert(isinstance(i[0], str))
	r = {}
	for i in l:
		r[i[0]] = i[1]
	return r


def test_squash():
	assert squash([("a", 1), ("b", 2), ("a", 3)]) == {"a": 3, "b": 2}


def newline(p, elem):
	p.lines.append([])
	for i in range(p.indent * p.indent_width):
		#keeps the attributes of the last node,
		#but lets see how this works in the ui..
		charadd(p.lines[-1], " ", p.atts)


def charadd(line, char, atts):
	#assert(isinstance(atts, list))
	a = squash(atts)
	#assert(isinstance(a, dict))
	line.append((char, a))

def attadd(atts, key, val):
	#assert(isinstance(key, str))
	atts.append((key, val))

def new_p(cols, frame):
	p = dotdict()
	p.width = cols
	p.indent_width = 4
	p.atts = []
	p.lines = [[]]
	p.arrows = []
	p.indent = 0
	p.frame = frame
	p.char_index = 0
	return p

def project(root, cols, frame):
	p = new_p(cols, frame)
	_project_elem(p, root)
	return p

def project_tags(tags, cols, frame):
	p = new_p(cols, frame)
	p._render_lines = {frame:[{}]}
	_project_tags(p, p, tags)
	return p

def _project_elem(p, elem):
	#assert(isinstance(elem, asselement.Element))
	#assert(isinstance(p.lines, list))
	#assert(isinstance(p.atts, list))
	#assert(isinstance(p.indent, int))
	p.char_index = 0
	#in theory, it could buy some cpu time to attadd/charadd these tags directly,
	#but actually they should rather be moved to Node.tags/Element.tags

	tags = [AttTag("node", elem)]
	tags += elem.tags()
	tags += [ColorTag(elem.brackets_color), TextTag(elem.brackets[1]), EndTag()]

	#results of eval
	if isinstance(elem, Node):
		if elem.runtime._dict.has_key("value") and elem.runtime._dict.has_key("evaluated"):
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

	elem._render_lines[p.frame] = {
		"startchar": len(p.lines[-1]),
		"startline": len(p.lines)-1}

	_project_tags(p, elem, tags)

	elem._render_lines[p.frame]["endchar"] = len(p.lines[-1])
	elem._render_lines[p.frame]["endline"] = len(p.lines)-1



def _project_tags(p, elem, tags):

	for tag in tags:
	#first some replaces
		if isinstance(tag, TextTag):
			tag = tag.text
		elif isinstance(tag, NewlineTag):
			tag = "\n"

		elif isinstance(tag, ChildTag):
			assert(isinstance(elem, assnodes.Node))
			assert(isinstance(elem.ch[tag.name], asselement.Element))
			tag = ElementTag(elem.ch[tag.name]) #get child
		elif isinstance(tag, WidgetTag):
			tag = ElementTag(elem.__dict__[tag.name]) #get widget #?

	#now real stuff
		if isinstance(tag, (str, unicode)):
			for char in tag:
				attadd(p.atts, "char_index", p.char_index)
				if char == "\n":
					newline(p, elem)
				else:
					if len(p.lines[-1]) >= p.width:
						newline(p, elem)
					charadd(p.lines[-1], char, p.atts)
				p.atts.pop()
				p.char_index += 1

		elif isinstance(tag, AttTag):
			attadd(p.atts, tag.key, tag.val)
		elif isinstance(tag, EndTag):
			p.atts.pop()
		elif isinstance(tag, ColorTag):
			attadd(p.atts, "color", tag.color)

		#recurse
		elif isinstance(tag, ElementTag):

			_project_tags(p, elem, [ColorTag(tag.element.brackets_color), TextTag(tag.element.brackets[0]), EndTag()])
			_project_elem(p, tag.element)

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
			raise Exception("is %s a tag?" % tag.__class__)




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
