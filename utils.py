import collections

def flatten_gen(x):
	for y in x:
		if isinstance(y, basestring) or not isinstance(y, list):
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


