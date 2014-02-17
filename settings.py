
import widgets
from nodes import *

class Setting(Templated):
	def __init__(self):
		super(Setting, self).__init__()
		self.register_event_types("on_change")
		self.oneliner = True

class FontSize(Setting):
	def __init__(self, value):
		super(FontSize, self).__init__()
		self.templates = [template([child("widget")])]
		self.set('widget', widgets.Number(value))

	@property
	def value(self):
		return int(self.widget.text)

class Fullscreen(Setting):
	def __init__(self):
		super(Fullscreen, self).__init__()
		self.templates = [template([child("widget")])]
		self.set('widget', widgets.Toggle(False))
		self.widget.push_handlers(on_edit = self.on_widget_edit)
	def on_widget_edit(self, widget):
		print "aaa"
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