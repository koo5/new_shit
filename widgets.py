# -*- coding: utf-8 -*-

"""textbox, button, toggle.."""

from pizco import Signal

from element import Element
from lemon_utils.lemon_logger import log
from lemon_utils.lemon_six import unicode
from tags import TextTag, ColorTag, EndTag, MemberTag, node_att, char_index_att
from keys import *


class Event(object):
	"""a base class for user events"""


class Widget(Element):
	def __init__(self, parent):
		super(Widget, self).__init__()
		self.parent = parent
	#def __repr__(s):
	#	return object.__repr__(s) + "(parent:'"+str(s.parent)+"')"


class Text(Widget):
	def __init__(self, parent, text):
		super(Text, self).__init__(parent)
		self.on_edit = Signal()
		self.color = (150,150,255,255)
		assert isinstance(text, unicode)
		self.text = text

	def render(self):
		return [TextTag(self.text)]
	
	def on_keypress(self, e):
		return self._keypress(e, e.atts[char_index_att])

	keys = ["text editing keys"]
	def _keypress(self, e, pos):

		# do not steal ctrl-delete event from others
		if e.mod & KMOD_CTRL:
			return False

		log("text widget editing on char_index %s"%pos)

		#editing keys
		if e.key == K_BACKSPACE	and pos > 0 and len(self.text) > 0 and pos < len(self.text)+2:
			self.text = self.text[0:pos-2] + self.text[pos-1:]
			self.root.delayed_cursor_move = -1

		elif e.key == K_DELETE and pos > 0 and len(self.text) > 0 and pos < len(self.text)+1:
			self.text = self.text[0:(pos-1)] + self.text[pos:]

		#text input
		elif e.uni \
			and e.key not in (K_DELETE, K_BACKSPACE, K_ESCAPE) \
			and 0 < pos < len(self.text)+2:
				self.text = self.text[:(pos-1)] + e.uni + self.text[(pos-1):]
				self.root.delayed_cursor_move = len(e.uni)

		else:
			return False
		#log(self.text + "len: " + len(self.text))
		self.dispatch_event('on_edit', self)
		return CHANGED

	@property
	def value(self):
		return self.text
	@value.setter
	def value(self, v):
		self.text = v

"""
class ShadowedText(Text):

	def __init__(self, parent, text, shadow):

		super(ShadowedText, self).__init__(parent, text)
		self.shadow = shadow

	def render(self):
		return [TextTag(self.text),
				ColorTag((130,130,130,255)),
				TextTag(self.shadow[len(self.text):]),
				EndTag()]

#	def len(self):
#		return len(self.text+self.shadow[len(self.text)])
"""
class Button(Widget):
	def __init__(self, parent, text="[button]", description = "?"):#🔳🔳🔳🔳]"):
		super(Button, self).__init__(parent)
		self.on_press = Signal(1)
		self.on_text = Signal(1)
		self.color = (255,150,150,255)
		self.text = text
	def on_mouse_press(self, button):
		ping()
		self.on_click.emit(self)
	keys = ["return, space: press button"]
	def on_keypress(self, e):
		if e.key == K_RETURN or e.key == K_SPACE:
			self.on_press.emit(self)
			return True
	def render(self):
		return [ColorTag(self.color),TextTag(self.text), EndTag()]

class Number(Text):
	"""Number widget inherits from text, contents are only int()'ed when needed"""	
	def __init__(self, parent, text, limits=(None,None)):
		super(Number, self).__init__(parent, text)
		self.text = str(text)
		self.limits = limits
		self.minus_button = Button(self, "-")
		self.plus_button = Button(self, "+")
		for b in (self.plus_button, self.minus_button):
			b.brackets = ('{','}')
			b.brackets_color = b.color = "number buttons"
		self.minus_button.on_click.connect(self.on_widget_click)
		self.minus_button.on_text. connect(self.on_widget_text)
		self.plus_button. on_click.connect(self.on_widget_click)
		self.plus_button. on_text. connect(self.on_widget_text)
		self.on_change = Signal(1)

	def render(self):
		return [MemberTag('minus_button'), TextTag(self.text), MemberTag('plus_button')]
	@property
	def value(self):
		try:
			return int(self.text)
		except:
			return float(self.text)
	@value.setter
	def value(self, v):
		self.text = str(v)
	def inc(self):
		if self.limits[1] == None or self.limits[1] > int(self.text):
			self.text = str(int(self.text)+1)
			self.on_change.emit(self)
	
	def dec(self):
		if self.limits[0] == None or self.limits[0] < int(self.text):
			self.text = str(int(self.text)-1)
			self.on_change.emit(self)
	
	def on_widget_click(self,widget):
		if widget == self.minus_button:
			self.dec()
		if widget == self.plus_button:
			self.inc()
	def on_widget_text(self,text):
		if text == "+":
			self.inc()
		if text == "-":
			self.dec()
	def on_mouse_press(self, button):
		if button == 4:
			self.inc()
		if button == 5:
			self.dec()

	def on_keypress(self, e):
		#since Number is a subclass of Text, with buttons, we substract the left button chars,
		#then pass it to Text's handler
		pos = e.atts[char_index_att] - 2
		return self._keypress(e, pos)


				
class NState(Widget):
	def __init__(self, parent, value, texts = ("to state 1", "to state 2", "to state 0")):
		super(NState, self).__init__(parent)
		self.on_change = Signal()
		self.value = value
		assert(0 <= value < len(texts))
		self.texts = texts
		self.color = "fg"
	def render(self):
		return [ColorTag(self.color), TextTag(self.text), EndTag()]
	@property
	def text(self):
		return self.texts[self.value]
	def toggle(self):
		self.value = self.value + 1
		if self.value == len(self.texts):
			self.value = 0
		self.on_change.emit(self)
	def on_mouse_press(self, button):
		self.toggle()
		return True
	keys = ["return, space: toggle"]
	def on_keypress(self, e):
		if e.key == K_RETURN or e.key == K_SPACE:
			self.toggle()
			return CHANGED

#NState uses a number, Toggle bool..

class Toggle(Widget):
	def __init__(self, parent, value, texts = ("checked", "unchecked")):
		super(Toggle, self).__init__(parent)
		self.on_change = Signal(1)
		self.value = value
		self.texts = texts
		self.color = "fg"
	def render(self):
		return [ColorTag(self.color), TextTag(self.text), EndTag()]
	@property
	def text(self):
		return self.texts[0] if self.value else self.texts[1]
	def toggle(self):
		self.value = not self.value
		self.on_change.emit(self)
	def on_mouse_press(self, button):
		self.toggle()
	keys = ["return, space: toggle"]
	def on_keypress(self, e):
		if e.key == K_RETURN or e.key == K_SPACE:
			self.toggle()
			return CHANGED
