
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


