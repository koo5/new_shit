
import widgets
from nodes import *

class Setting(Syntaxed):
	def __init__(self):
		super(Setting, self).__init__()
		self.register_event_types("on_change")
		self.oneliner = True

class FontSize(Setting):
	def __init__(self, value):
		super(FontSize, self).__init__()
		self.syntaxes = [[ch("widget")]]
		self.setw('widget', widgets.Number(value))

	@property
	def value(self):
		return int(self.widget.text)

class Fullscreen(Setting):
	def __init__(self):
		super(Fullscreen, self).__init__()
		self.syntaxes = [[ch("widget")]]
		self.setw('widget', widgets.Toggle(False))
		self.widget.push_handlers(on_change = self.on_widget_edit)
	def on_widget_edit(self, widget):
		self.dispatch_event('on_change', self)

	@property
	def value(self):
		return self.widget.value

"""
todo:
move the settings tree here?
must add:
no-color
invert-color
"""
