# -*- coding: utf-8 -*-


import pyglet, pygame
import element
from logger import log, ping
from tags import TextTag, ColorTag, EndTag, WidgetTag


class Widget(element.Element):
	def __init__(self, parent):
		self.parent = parent

class Text(Widget):
	def __init__(self, parent, text):
		super(Text, self).__init__(parent)
		self.register_event_types('on_edit')
		self.color = (150,150,255,255)
		self.text = text
		
	def get_caret_position(self):
		return self.root.caret_position - self.doc.positions[self]
		
	def render(self):
		return [TextTag(self.text)]
	
	def on_keypress(self, e):
		pos = e.pos
		if e.key == pygame.K_BACKSPACE:
			if pos > 0 and len(self.text) > 0 and pos <= len(self.text):
				self.text = self.text[0:pos -1] + self.text[pos:]
#				log(self.text)
				self.root.post_render_move_caret = -1
		elif e.key == pygame.K_DELETE:
			if pos >= 0 and len(self.text) > 0 and pos < len(self.text):
				self.text = self.text[0:pos] + self.text[pos + 1:]
		elif e.key == pygame.K_ESCAPE:
			return False
		elif e.key == pygame.K_RETURN:
			return False
		elif e.uni:
			self.text = self.text[:pos] + e.uni + self.text[pos:]
			self.root.post_render_move_caret = len(e.uni)
		else: return False
		#log(self.text + "len: " + len(self.text))
		self.dispatch_event('on_edit', self)
		return True

	
	def on_text_motion(self, motion, select=False):
		ping()
		if motion == pyglet.window.key.MOTION_BACKSPACE:
			position = self.get_caret_position()
			if position > 0:
				self.text = self.text[:position-1]+self.text[position:]
			self.dispatch_event('on_edit', self)
			self.win.post_render_move_caret = -1
		else:
			return False
		return True


class ShadowedText(Text):

	def __init__(self, parent, text, shadow):

		super(ShadowedText, self).__init__(parent, text)
		self.shadow = shadow

	def render(self):
		return [TextTag(self.text),
				ColorTag((130,130,130,255)),
				TextTag(self.shadow[len(self.text):]),
				EndTag()]

	def len(self):
		return len(self.text+self.shadow[len(self.text)])
		
class Button(Widget):
	def __init__(self, parent, text="[      ]"):#🔳🔳🔳🔳]"):
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
		return [TextTag(self.text)]

class Number(Text):
	"""Number widget inherits from text, contents are only int()'ed when needed"""	
	def __init__(self, parent, text, limits=(None,None)):
		super(Number, self).__init__(parent, text)
		self.text = str(text)
		self.limits = limits
		self.minus_button = Button(self, "-")
		self.plus_button = Button(self, "+")
		self.minus_button.push_handlers(on_click=self.on_widget_click, on_text=self.on_widget_text)
		self.plus_button.push_handlers(on_click=self.on_widget_click, on_text=self.on_widget_text)
		self.register_event_types('on_change')

	def render(self):
		return [WidgetTag('minus_button'), TextTag(self.text), WidgetTag('plus_button')]
	@property
	def value(self):
		return int(self.text)

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

				
class Toggle(Widget):
	def __init__(self, parent, value):
		super(Toggle, self).__init__(parent)
		self.register_event_types('on_change')
		self.value = value
	def render(self):
		return [TextTag(self.text)]
	@property
	def text(self):
		return "checked" if self.value else "unchecked"
	def on_mouse_press(self, button):
		self.value = not self.value
		#self.dispatch_event('on_change', self)
		





