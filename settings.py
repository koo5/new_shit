
import widgets
from nodes import *

class Setting(Syntaxed):
	def __init__(self):
		super(Setting, self).__init__()
		self.register_event_types("on_change")

class FontSize(Setting):
	def __init__(self, value):
		super(FontSize, self).__init__()
		self.syntaxes = [[w("widget")]]
		self.widget = widgets.Number(self, value)

	@property
	def value(self):
		return int(self.widget.text)

class Fullscreen(Setting):
	def __init__(self):
		super(Fullscreen, self).__init__()
		self.syntaxes = [[w("widget")]]
		self.widget = widgets.Toggle(self, False)
		self.widget.push_handlers(on_change = self.on_widget_edit)
	def on_widget_edit(self, widget):
		self.dispatch_event('on_change', self)

	@property
	def value(self):
		return self.widget.value

class ProjectionDebug(Setting):
	def __init__(self):
		super(ProjectionDebug, self).__init__()
		self.syntaxes = [[w("widget")]]
		self.widget = widgets.Toggle(self, False)
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
