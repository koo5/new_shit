
import os
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
"""
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
"""
class KeyRepeat(Setting):
	def __init__(self):
		super(KeyRepeat, self).__init__()
		self.syntaxes = [[t("rate:"), w("rate"), t("first repeat delay"), w("delay")]]
		
		s = os.popen('xset -q  | grep "repeat delay"').read().split()
	
		repeat_delay = int(s[3])
		repeat_rate = int(s[6])

		self.delay = widgets.Number(self, repeat_delay)
		self.rate = widgets.Number(self, repeat_rate)
		
		self.rate.push_handlers(on_change = self.on_widget_edit)
		self.delay.push_handlers(on_change = self.on_widget_edit)
		
#		self.on_widget_edit("banana")
		
	def on_widget_edit(self, widget):
		#self.dispatch_event('on_change', self)
		pygame.key.set_repeat(self.delay.value, 1000/self.rate.value)
		log("pygame.key.set_repeat(self.delay.value=%s, 1000/self.rate.value=%s"%(self.delay.value, self.rate.value))



"""
todo:
move the settings tree here?
must add:
no-color
invert-color
"""
