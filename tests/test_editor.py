from unittest import TestCase

__author__ = 'kook'

from server_frames import *
import tags

class TestEditor(TestCase):
	def test_element_under_cursor(self):
		editor.set_atts({tags.node_att: 123})
		assert editor.element_under_cursor() == 123
