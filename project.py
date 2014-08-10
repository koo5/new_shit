# -*- coding: utf-8 -*-


"""
take a list of tags (see tags.py) or an element and render everything into
lines of tuples containing characters to be displayed on screen and their
attributes (most importantly the element the char belongs to and color)
line is a list of tuples: (character, attributes)
"""

from tags import *
from logger import ping, log
import colors
from nodes import Node, Parser
from dotdict import dotdict

if __debug__:
	import element as asselement
	import nodes as assnodes



def squash(l):
	"""squash a stack of dicts into a single dict"""
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


DONE = 1
def newline(p, elem):
	p.lines.append([])
	if p.rows_limit and len(p.lines) > p.rows_limit:
		return DONE
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

def new_p(cols, frame, rows_limit):
	"""build up the data structure that holds the parameters, state and results of the projection"""
	p = dotdict()
	p.width = cols
	p.indent_width = 4
	p.atts = []
	p.lines = [[]]
	p.arrows = []
	p.indent = 0
	p.frame = frame
	p.char_index = 0
	p.rows_limit = rows_limit
	return p

def project(root, cols, frame, rows_limit = False):
	p = new_p(cols, frame, rows_limit)
	_project_elem(p, root)
	return p

def project_tags(tags, cols, frame, rows_limit = False):
	p = new_p(cols, frame, rows_limit)
	p._render_lines = {frame:[{}]}
	_project_tags(p, p, tags)
	return p

def _project_elem(p, elem):
	#assert(isinstance(elem, asselement.Element))
	#assert(isinstance(p.lines, list))
	#assert(isinstance(p.atts, list))
	#assert(isinstance(p.indent, int))
	p.char_index = 0

	#_render_lines holds information about how the element was rendered
	#in a particular frame
	elem._render_lines[p.frame] = {
		"startchar": len(p.lines[-1]),
		"startline": len(p.lines)-1}

	for tags in elem.tags():
		if _project_tags(p, elem, tags) == DONE:
			return DONE

	elem._render_lines[p.frame]["endchar"] = len(p.lines[-1])
	elem._render_lines[p.frame]["endline"] = len(p.lines)-1



def _project_tags(p, elem, tags):

	if isinstance(tags, list):
		for tag in tags:
			if _project_tags(p, elem, tag) == DONE:
				return DONE
	else:
		tag = tags
	#first some simple replacements
		if isinstance(tag, TextTag):
			tag = tag.text
		elif isinstance(tag, NewlineTag):
			tag = "\n"

		elif isinstance(tag, ChildTag):
			assert(isinstance(elem, assnodes.Node))
			assert(isinstance(elem.ch[tag.name], asselement.Element))
			tag = ElementTag(elem.ch[tag.name]) #get child of Syntaxed
		elif isinstance(tag, WidgetTag):
			#get the element as an attribute
			#i think this should be getattr
			tag = ElementTag(elem.__dict__[tag.name])

	#now real stuff
		if isinstance(tag, (str, unicode)):
			for char in tag:
				attadd(p.atts, "char_index", p.char_index)
				if char == "\n":
					if newline(p, elem) == DONE:
						return DONE
				else:
					if len(p.lines[-1]) >= p.width:
						if newline(p, elem) == DONE:
							return DONE
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
			#an opening bracket belongs to the parent node. its weird.
			#cursor always acts on the char to the right of it
			#so when it is on an opening bracket of a child,
			#it is still "in" the parent
			if _project_tags(p, elem, [AttTag("opening bracket", True), ColorTag(tag.element.brackets_color), TextTag(tag.element.brackets[0]), EndTag(), EndTag()]) == DONE:
				return DONE
			if _project_elem(p, tag.element) == DONE:
				return DONE

	#some more stuff
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
	"""return coordinates of element in rendered lines"""
	assert(isinstance(node, asselement.Element))
	for r,line in enumerate(lines):
		for c,char in enumerate(line):
			if char[1]['node'] == node:
				return c, r
	return None


if __debug__:
	test_squash()

