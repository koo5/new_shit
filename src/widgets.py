# -*- coding: utf-8 -*-

"""textbox, button, toggle.."""

from lemon_utils.pizco_signal.util import Signal

from element import Element, CHANGED
from lemon_utils.lemon_six import unicode
from tags import *
from keys import *
from lemon_colors import colors


import logging
logger=logging.getLogger("root")
info=logger.info
log=logger.debug

class Widget(Element):
	def __init__(s, parent):
		super(Widget, s).__init__()
		s.parent = parent
	#def __repr__(s):
	#	return object.__repr__(s) + "(parent:'"+str(s.parent)+"')"


class Text(Widget):
	def __init__(s, parent, text):
		super().__init__(parent)
		s.on_edit = Signal(1)
		s.color = colors.widget_color
		assert isinstance(text, unicode)
		s.text = text
		s.brackets = ['','']

	def copy(s):
		r = s.__class__(s.parent, s.text)
		r.text = s.text
		return r

	def render(s):
		return [editable_start_tag, TextTag(s.text), editable_end_tag]

	@property
	def value(s):
		return s.text
	@value.setter
	def value(s, v):
		s.text = v

	def after_edit(s, move):
		s.root.delayed_cursor_move.chars += move
		s.on_edit.emit(s)
		return CHANGED


class Button(Widget):
	def __init__(s, parent, text="[button]", description = "?"):#?
		super().__init__(parent)
		s.on_press = Signal(1)
		s.on_text = Signal(1)
		s.color = colors.button
		s.text = text

	def copy(s):
		r = s.__class__()
		r.text = s.text
		return r

	def on_mouse_press(s, button):
		s.on_click.emit(s)
		return CHANGED

	def render(s):
		return [ColorTag(s.color),TextTag(s.text), EndTag()]

class Number(Widget):
	def __init__(s, parent, text, limits=(None,None)):
		super().__init__(parent)
		s.limits = limits
		s.text_widget = Text(s, str(text))
		s.minus_button = Button(s, "-")
		s.plus_button = Button(s, "+")
		for b in (s.plus_button, s.minus_button):
			b.brackets = ('[',']')
			b.brackets_color = b.color = colors.number_buttons
		s.minus_button.on_press.connect(s.on_widget_click)
		s.minus_button.on_text. connect(s.on_widget_text)
		s.plus_button. on_press.connect(s.on_widget_click)
		s.plus_button. on_text. connect(s.on_widget_text)
		s.on_change = Signal(1)
		s.text_widget.on_edit.connect(s._on_text_change) # ^.^

	def copy(s):
		r = s.__class__()
		r.text = s.text
		r.limits = s.limits
		return r

	def _on_text_change(s, widget):
		s.on_change.emit(s)

	def render(s):
		return [MemberTag('minus_button'), MemberTag('text_widget'), MemberTag('plus_button')]

	@property
	def value(s):
		try:
			return int(s.text)
		except:
			return float(s.text)
	@value.setter
	def value(s, v):
		s.text = str(v)

	@property
	def text(s):
		return s.text_widget.text
	@text.setter
	def text(s, x):
		s.text_widget.text = x

	def inc(s):
		if s.limits[1] == None or s.limits[1] > int(s.text):
			s.text = str(int(s.text)+1)
			s.on_change.emit(s)

	def dec(s):
		if s.limits[0] == None or s.limits[0] < int(s.text):
			s.text = str(int(s.text)-1)
			s.on_change.emit(s)

	def on_widget_click(s,widget):
		if widget == s.minus_button:
			s.dec()
		if widget == s.plus_button:
			s.inc()

	def on_widget_text(s,text):
		if text == "+":
			s.inc()
		if text == "-":
			s.dec()

	def on_mouse_press(s, button):
		""" handles scrollwheel	"""
		if button == 4:
			s.inc()
		if button == 5:
			s.dec()



class NState(Widget):
	def __init__(s, parent, value, texts = ("to state 1", "to state 2", "to state 0")):
		super(NState, s).__init__(parent)
		s.on_change = Signal(1)
		s.value = value
		assert(0 <= value < len(texts))
		s.texts = texts
		s.color = colors.fg

	def copy(s):
		r = s.__class__()
		r.texts = s.texts
		r.value = s.value
		return r

	def render(s):
		return [ColorTag(s.color), TextTag(s.text), EndTag()]

	@property
	def text(s):
		return s.texts[s.value]

	def on_mouse_press(s, button):
		s.toggle(555)
		return True



#NState uses a number, Toggle bool..

class Toggle(Widget):
	def __init__(s, parent, value, texts = ("checked", "unchecked")):
		super(Toggle, s).__init__(parent)
		s.on_change = Signal(1)
		s.value = value
		s.texts = texts
		s.color = colors.fg
	def render(s):
		return [ColorTag(s.color), TextTag(s.text), EndTag()]
	@property
	def text(s):
		return s.texts[0] if s.value else s.texts[1]
	def on_mouse_press(s, button):
		s.toggle(555)
		return True
