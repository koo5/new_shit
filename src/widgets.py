# -*- coding: utf-8 -*-

"""textbox, button, toggle.."""

from lemon_utils.pizco_signal.util import Signal

from element import Element, CHANGED
from lemon_utils.lemon_logging import log
from lemon_utils.lemon_six import unicode
from tags import *
from keys import *
from lemon_colors import colors


class Widget(Element):
	def __init__(self, parent):
		super(Widget, self).__init__()
		self.parent = parent
	#def __repr__(s):
	#	return object.__repr__(s) + "(parent:'"+str(s.parent)+"')"


class Text(Widget):
	def __init__(self, parent, text):
		super().__init__(parent)
		self.on_edit = Signal(1)
		self.color = colors.widget_color
		assert isinstance(text, unicode)
		self.text = text
		self.brackets = ['','']

	def render(self):
		return [editable_start_tag, TextTag(self.text), editable_end_tag]

	@property
	def value(self):
		return self.text
	@value.setter
	def value(self, v):
		self.text = v

	def after_edit(s, move):
		s.root.delayed_cursor_move.chars += move
		s.on_edit.emit(s)
		return CHANGED


class Button(Widget):
	def __init__(self, parent, text="[button]", description = "?"):#?
		super().__init__(parent)
		self.on_press = Signal(1)
		self.on_text = Signal(1)
		self.color = colors.button
		self.text = text

	def on_mouse_press(self, button):
		self.on_click.emit(self)
		return CHANGED

	def render(self):
		return [ColorTag(self.color),TextTag(self.text), EndTag()]

class Number(Widget):
	def __init__(self, parent, text, limits=(None,None)):
		super().__init__(parent)
		self.limits = limits
		self.text_widget = Text(self, str(text))
		self.minus_button = Button(self, "-")
		self.plus_button = Button(self, "+")
		for b in (self.plus_button, self.minus_button):
			b.brackets = ('[',']')
			b.brackets_color = b.color = colors.number_buttons
		self.minus_button.on_press.connect(self.on_widget_click)
		self.minus_button.on_text. connect(self.on_widget_text)
		self.plus_button. on_press.connect(self.on_widget_click)
		self.plus_button. on_text. connect(self.on_widget_text)
		self.on_change = Signal(1)
		self.text_widget.on_edit.connect(self._on_text_change) # ^.^

	def _on_text_change(self, widget):
		self.on_change.emit(self)

	def render(self):
		return [MemberTag('minus_button'), MemberTag('text_widget'), MemberTag('plus_button')]

	@property
	def value(self):
		try:
			return int(self.text)
		except:
			return float(self.text)
	@value.setter
	def value(self, v):
		self.text = str(v)

	@property
	def text(s):
		return s.text_widget.text
	@text.setter
	def text(s, x):
		s.text_widget.text = x

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
		""" handles scrollwheel	"""
		if button == 4:
			self.inc()
		if button == 5:
			self.dec()



class NState(Widget):
	def __init__(self, parent, value, texts = ("to state 1", "to state 2", "to state 0")):
		super(NState, self).__init__(parent)
		self.on_change = Signal(1)
		self.value = value
		assert(0 <= value < len(texts))
		self.texts = texts
		self.color = colors.fg

	def render(self):
		return [ColorTag(self.color), TextTag(self.text), EndTag()]

	@property
	def text(self):
		return self.texts[self.value]

	def on_mouse_press(self, button):
		return self.toggle()



#NState uses a number, Toggle bool..

class Toggle(Widget):
	def __init__(self, parent, value, texts = ("checked", "unchecked")):
		super(Toggle, self).__init__(parent)
		self.on_change = Signal(1)
		self.value = value
		self.texts = texts
		self.color = colors.fg
	def render(self):
		return [ColorTag(self.color), TextTag(self.text), EndTag()]
	@property
	def text(self):
		return self.texts[0] if self.value else self.texts[1]
	def on_mouse_press(self, button):
		self.toggle()
