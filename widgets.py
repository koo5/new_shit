# -*- coding: utf-8 -*-


import pygame
import element
from logger import log, ping
from tags import TextTag, ColorTag, EndTag, WidgetTag


class Widget(element.Element):
	def __init__(self, parent):
		super(Widget, self).__init__()
		self.parent = parent

class Text(Widget):
	def __init__(self, parent, text):
		super(Text, self).__init__(parent)
		self.register_event_types('on_edit')
		self.color = (150,150,255,255)
		self.text = text

	def render(self):
		return [TextTag(self.text)]
	
	def on_keypress(self, e):
		pos = e.atts["char_index"]
		return self._keypress(e, pos)

	def _keypress(self, e, pos):
		#first things that a text field should pass up
		if e.mod & pygame.KMOD_CTRL:
			return False
		elif e.key == pygame.K_ESCAPE:
			return False
		elif e.key == pygame.K_RETURN:
			return False

		#editing keys
		if e.key == pygame.K_BACKSPACE:
			if pos > 0 and len(self.text) > 0 and pos <= len(self.text):
				self.text = self.text[0:pos -1] + self.text[pos:]
#				log(self.text)
				self.root.post_render_move_caret = -1
		elif e.key == pygame.K_DELETE:
			if pos >= 0 and len(self.text) > 0 and pos < len(self.text):
				self.text = self.text[0:pos] + self.text[pos + 1:]

		#letters
		elif e.uni:
			self.text = self.text[:pos] + e.uni + self.text[pos:]
			self.root.post_render_move_caret = len(e.uni)

		else: return False
		#log(self.text + "len: " + len(self.text))
		self.dispatch_event('on_edit', self)
		return True

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
		self.register_event_types('on_click, on_text')
		self.color = (255,150,150,255)
		self.text = text
	def on_mouse_press(self, button):
		ping()
		self.dispatch_event('on_click', self)
	def on_keypress(self, e):
		ping()
		if e.key == pygame.K_RETURN or e.key == pygame.K_SPACE:
			self.dispatch_event('on_click', self)
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
		self.minus_button.push_handlers(on_click=self.on_widget_click, on_text=self.on_widget_text)
		self.plus_button.push_handlers(on_click=self.on_widget_click, on_text=self.on_widget_text)
		self.register_event_types('on_change')

	def render(self):
		return [WidgetTag('minus_button'), TextTag(self.text), WidgetTag('plus_button')]
	@property
	def value(self):
		return int(self.text)
	@value.setter
	def value(self, v):
		self.text = str(v)
	def inc(self):
		if self.limits[1] == None or self.limits[1] > int(self.text):
			self.text = str(int(self.text)+1)
			self.dispatch_event('on_change', self)
	
	def dec(self):
		if self.limits[0] == None or self.limits[0] < int(self.text):
			self.text = str(int(self.text)-1)
			self.dispatch_event('on_change', self)
	
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
		"""crudity crudity messity mess!"""
		pos = e.atts["char_index"] - 2
		return self._keypress(e, pos)


				
class NState(Widget):
	def __init__(self, parent, value, texts = ("to state 1", "to state 2", "to state 0")):
		super(NState, self).__init__(parent)
		self.register_event_types('on_change')
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
		self.dispatch_event('on_change', self)
	def on_mouse_press(self, button):
		self.toggle()
		return True
	def on_keypress(self, e):
		if e.key == pygame.K_RETURN or e.key == pygame.K_SPACE:
			self.toggle()
			return True

#NState uses a number, Toggle bool..

class Toggle(Widget):
	def __init__(self, parent, value, texts = ("checked", "unchecked")):
		super(Toggle, self).__init__(parent)
		self.register_event_types('on_change')
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
		self.dispatch_event('on_change', self)
	def on_mouse_press(self, button):
		self.toggle()
	def on_keypress(self, e):
		if e.key == pygame.K_RETURN or e.key == pygame.K_SPACE:
			self.toggle()
			return True
