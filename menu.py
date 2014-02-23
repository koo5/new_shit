from tags import TextTag, ColorTag, EndTag, NewlineTag
from widgets import Widget

#a widget for now...the actual rendering..should be thru a special tag i guess
class Menu(Widget):
	def __init__(self, parent, items):
		super(Menu, self).__init__(parent)
		self.register_event_types('on_click')
		self.color = (100,230,50,255)
		self.items = items
		self.sel = -1

	def render(self):
		r = []
		for i, item in enumerate(self.items):
			color = (255,100,100,255) if self.sel == i else self.color
			r += [NewlineTag()+ColorTag(color), TextTag(item)]
		r.append(NewlineTag())				


