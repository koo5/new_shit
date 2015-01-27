
try:
	from collections import OrderedDict as odict
except:#be compatible with older python (2.4?)
	from lemon_utils.odict import OrderedDict as odict

def updated_with(d, d2):
	"""update d with d2 and return it"""
	d.update(d2)
	return d
odict.updated_with = updated_with

def plus(d, d2):
	"""copy d, update it with d2 and return"""
	r = d.copy()
	r.update(d2)
	return r
odict.plus = plus


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



class Evil(object):
	"""this is an Evil default object. if you ran into it, you made a wrong turn somewhere"""
	__slots__ = ['note']
	def __init__(s, note="damn"):
		s.note = note
	def __repr__(s):
		return str(s.note)


from itertools import *


def batch(it, n=100):
	m = n - 1
	while True: #islice wont throw an ExhaustedIterator exception when its source is exhausted
		# so we peek one element with next(), then chain it to the isliced rest. next throws
		# when the source is exhausted, thus ending this function
		yield chain([next(it)], islice(it, 0, m))


def uniq(lst):
   r = []
   for i in lst:
       if i not in r:
           r.append(i)
   return r

def clamp(x, min, max):
	if x < min:
		return min
	elif x >= max:
		return max
	else:
		return x