# -*- coding: utf-8 -*-

"""
take a list of tags (see tags.py) or an element and render everything into
lines of tuples containing characters to be displayed on screen and their
attributes (most importantly the element the char belongs to and color)
line is a list of tuples: (character, attributes)
"""

from __future__ import unicode_literals


from lemon_six import str_and_uni
from tags import *
from lemon_logger import ping, log
from nodes import Node, Parser
from dotdict import dotdict

if __debug__:
	import element as asselement
	import nodes as assnodes

#__slow_debug__ = False #todo:lemon_options?

# region utils

#def squash(l):
#	"""squash a stack of tuples into a single dict"""
#	ping()
#	if __debug__:
#		assert(isinstance(l, list))
#		for i in l:
#			assert(isinstance(i, tuple))
#			assert(len(i) == 2)
#			assert(isinstance(i[0], str))

#	r = {}
#	for i in l:
#		r[i[0]] = i[1]
#	return r
#	return dict(l)
squash = dict

def test_squash():
	assert squash([("a", 1), ("b", 2), ("a", 3)]) == {"a": 3, "b": 2}


DONE = 1#kinda an enum

def newline(p, elem):
	if p.rows_limit and len(p.lines) == p.rows_limit:
		return DONE
	l = []
	p.lines.append(l)
	a = squash(p.atts)##i basically inlined charadd into here, dunno if thats useful
	for i in xrange(p.indent * p.indent_width):
		#keeps the attributes of the last node,
		#but lets see how this works in the ui..
		#charadd(l, " ", p.atts)
		l.append((" ", a))

def charadd(line, ch, atts):
	#assert(isinstance(atts, list))
	a = squash(atts)
	#assert(isinstance(a, dict))
	line.append((ch, a))

def attadd(atts, key, val):
	#assert(isinstance(key, str))
	atts.append((key, val))

class projection_results(object):
	"""parameters, state and results of projection"""
	__slots__ = "width indent_width atts lines arrows indent frame char_index rows_limit _render_lines".split()

	def __init__(s, cols, frame, rows_limit):
		s.width = cols
		s.indent_width = 4
		s.atts = []
		s.lines = [[]]
		s.arrows = []
		s.indent = 0
		s.frame = frame
		s.char_index = 0
		s.rows_limit = rows_limit
		s._render_lines = None


# endregion
# region the meat

"""
def collect_tags(tags):
	for tag in tags:
		if isinstance(tag, list):
			for t in _collect_tags(tags):
				yield t
		elif isinstance(tag, ChildTag):
			for t in _collect_tags(elem.ch[tag.name]):
				yield t
			tag = ElementTag()
"""
#https://docs.python.org/2/library/collections.html#collections.deque
#(tags.color, (3,3,3))..



def project(root, cols, frame, rows_limit = False):
	"""the main entry point to the projection functionality. This is what is used now. The collecting of tags is coupled with the rendering"""
	p = projection_results(cols, frame, rows_limit)
	_project_elem(p, root)
	return p

def project_tags(tags, cols, frame, rows_limit = False):
	p = projection_results(cols, frame, rows_limit)
	p._render_lines = {frame:[{}]}#?
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

	if _project_tags(p, elem, elem.tags()) == DONE:
		return DONE

	elem._render_lines[p.frame]["endchar"] = len(p.lines[-1])
	elem._render_lines[p.frame]["endline"] = len(p.lines)-1


import collections

def _project_tags(p, elem, tag):
	if type(tag) == unicode:
		return _project_string(p, tag, elem)

	elif type(tag) == TextTag:
		return _project_string(p, tag.text, elem)

	#elif isinstance(tag, collections.Iterable):
	#	for t in tag:
	#		if _project_tags(p, elem, t) == DONE:
	#			return DONE


	try:#lets try if we can iterate over tag (hard to tell if its a list, generator or wut and how)
		expecting_exception_now = True
		for t in tag:
			expecting_exception_now = False
			if _project_tags(p, elem, t) == DONE:
				return DONE
		return
	except:
		if not expecting_exception_now:
			raise
		#otherwise pass

	if type(tag) == ChildTag:
			#assert(isinstance(elem, assnodes.Node))
			#assert(isinstance(elem.ch[tag.name], asselement.Element))
		return _project_elem(p, elem.ch[tag.name])

	elif type(tag) == MemberTag:
			#get the element as an attribute
			#i think this should be getattr, but it seems to work
		return _project_elem(p, elem.__dict__[tag.name])

	elif type(tag) == ElementTag:
		return _project_elem(p, tag.element)

	elif type(tag) == EndTag:
		p.atts.pop()

	elif type(tag) == AttTag:
		attadd(p.atts, tag.key, tag.val)

	elif type(tag) == ColorTag:
		attadd(p.atts, "color", tag.color)

	elif type(tag) == IndentTag:
		p.indent+=1

	elif type(tag) == DedentTag:
		p.indent-=1

	elif type(tag) == ArrowTag:
		p.arrows.append((len(p.lines[-1]), len(p.lines) - 1, tag.target))

	else:
		raise Exception("is %s a tag?, %s" % (repr(tag), elem))


def _project_string(p, tag, elem):
	for char in tag:
		attadd(p.atts, "char_index", p.char_index)
		#p.atts.append(("char_index", p.char_index))
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

#somewhat optimized version
def _project_string(p, tag, elem):
	p_width = p.width
	p_atts = p.atts
	p_atts.append(("char_index", p.char_index))
	line = p.lines[-1]
	line_append = line.append
	for char in tag:
		if char == "\n":
			if newline(p, elem) == DONE:
				return DONE
			line = p.lines[-1]
			line_append = line.append
		else:
			if len(line) >= p_width:
				if newline(p, elem) == DONE:
					return DONE
				line = p.lines[-1]
				line_append = line.append
			line_append((char, dict(p_atts)))
		p.char_index += 1
		p_atts[-1] = ("char_index", p.char_index)
	p.atts.pop()


def find(node, lines):
	"""return coordinates of element in rendered lines"""
	assert(isinstance(node, asselement.Element))
	for r,line in enumerate(lines):
		for c,char in enumerate(line):
			if char[1]['node'] == node:
				return c, r
	return None

# endregion

if __debug__:
	test_squash()

