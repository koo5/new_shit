from types import GeneratorType

import lemon_platform

from tags import *


def collect_elem(elem):
	return _collect_tags(elem, elem.tags())

def collect_tags(elem, tags):
	return _collect_tags(elem, elem.tags())

def _collect_tags(elem, tags):
	for tag in tags:
		if type(tag) in (GeneratorType, list):
			for i in _collect_tags(p, elem, tag):
				yield i

		elif type(tag) == TextTag:
			yield tag.text

		elif type(tag) == ChildTag:
			e = elem.ch[tag.name]
			for i in _collect_tags(p, e, e.tags()):
				yield i

		elif type(tag) == MemberTag:
			e = elem.__dict__[tag.name] #get the element as an attribute #i think this should be getattr, but it seems to work
			for i in _collect_tags(p, e, e.tags()):
				yield i

		elif type(tag) == ElementTag:
			e = tag.element
			for i in _collect_tags(p, e, e.tags()):
				yield i

		else:
			yield tag


