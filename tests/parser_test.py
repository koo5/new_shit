
from __future__ import unicode_literals

import nodes
from keys import *


from lemon import KeypressEvent
def test(p):
	p.items = []
	p.add("xxx")
	assert p.items == ["xxx"]

	#item index, cursor position in item, event
	p.edit_text(0, 0, KeypressEvent(
		[],	0, K_BACKSPACE, 0))

	assert p.items == ["xxx"]

	p.edit_text(0, 3, KeypressEvent(
		[],	0, K_BACKSPACE, 0))

	assert p.items == ["xx"]

	p.menu_item_selected(p.menu_for_item()[1])

	assert len(p.items) == 1
	assert isinstance(p.items[0], nodes.Node)

	p.add('yy')

	assert len(p.items) == 2
	assert isinstance(p.items[0], nodes.Node)
	assert p.items[1] == "yy", p.items[1]


