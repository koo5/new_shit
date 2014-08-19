import collections
from lemon_six import str_and_uni

def flatten_gen(x):
	for y in x:
		if isinstance(y, str_and_uni) or not isinstance(y, list):
			yield y
		else:
			for z in flatten_gen(y):
				yield z

def flatten(g):
	return list(flatten_gen(g))

def test_flatten():
	i = [3,[4,5],[[6,[7],8]]]
	o = flatten(i)
	assert o == [3,4,5,6,7,8], o

test_flatten()


