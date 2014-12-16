
from __future__ import unicode_literals

from lemon_utils.lemon_six import unicode

try:
	from collections import OrderedDict as odict
except:#be compatible with older python (2.4?)
	from lemon_utils.odict import OrderedDict as odict

def updated(d, d2):
	"""update d with d2 and return it"""
	d.update(d2)
	return d

odict.updated = updated

def flatten_gen(x):
	for y in x:
		if not isinstance(y, list):
			yield y
		else:
			for z in flatten_gen(y):
				yield z

def flatten(g):
	"""i use flatten, then iterate over the resulting list,
	in quite a few places. It maybe makes debugging easier and
	i dont actually know how to visitor pattern."""
	return list(flatten_gen(g))

def test_flatten():
	i = [3,[4,5],[[6,[7],8]]]
	o = flatten(i)
	assert o == [3,4,5,6,7,8], o

test_flatten()

class Evil(object):
	"""this is an Evil default object. if you ran into it, you made a wrong turn somewhere"""
	__slots__ = ['note']
	def __init__(s, note="damn"):
		s.note = note
	def __repr__(s):
		return str(s.note)
