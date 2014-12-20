from unittest import TestCase

from utils import flatten


class TestFlatten(TestCase):
	def test_flatten(self):
		i = [3,[4,5],[[6,[7],8]]]
		o = flatten(i)
		assert o == [3,4,5,6,7,8], o
