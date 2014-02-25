# -*- coding: utf-8 -*-


"""
functon project takes a list of tags created by root.tags()
 and outputs a list of lines
 line is a list of tuples: (character, attributes)

 break line on "\n"
 later: break too long lines
"""

from tags import *

"optimization: switch from dicts(one keyed) to tuples"
def squash(a):
	"""merges a list of dicts into a single dict
	(currently just dicts containing a single value)
	"""
	r = {}
	for i in a:
		r[i.items()[0][0]] = i.items()[0][1]
	return r

def test_squash():
	if squash([{"a": 1}, {"b": 2}, {"a": 3}]) != {"a": 3, "b": 2}:
		raise Exception()

def project(tags, indent_spaces, debug):
	lines = [[]]
	line = lines[0]
	atts = []
	indent = 0


	for tag in tags:
		if isinstance(tag, NewlineTag):
			tag = TextTag("\n")
		
		if isinstance(tag, AttTag):
			atts.append(tag.attribute)
		if isinstance(tag, NodeTag):
			atts.append({"node": tag.node})
			if debug: line.append(">")#⇾")
		if isinstance(tag, ColorTag):
			atts.append({"color": tag.color})
		if isinstance(tag, EndTag):
			if debug: line.append("<")#⇽")
			atts.pop()
		if isinstance(tag, IndentTag):
			indent+=1
		if isinstance(tag, DedentTag):
			indent-=1
		if isinstance(tag, BackspaceTag):
			if len(line) <> tag.spaces:
				print "cant backspace that much"
			line = line[:-tag.spaces]
		if isinstance(tag, TextTag):
			for i, char in enumerate(tag.text):
				if char == "\n":
					lines.append([])
					line = lines[len(lines)-1]

					for i in range(indent * indent_spaces):
						#keeps the attributes of the last node,
						#but lets see..
						line.append((" ", squash(atts)))

				else:
					atts.append({"char_index": i})
					line.append((char, squash(atts)))
					atts.pop() #char_index

	return lines


test_tags = [
		#output of root.render() will look something like that:
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


def test_project():

	lines = project(test_tags, indent_spaces = 4, debug=False)
	return lines


"""
def render(lines):
	for l, line in enumerate(screen):
		for c, char in enumerate(line);
			#render char on screen
"""

test_squash()
test_project()

print "thumbs up"
