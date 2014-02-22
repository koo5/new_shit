# -*- coding: utf-8 -*-


import pyglet
import element
from logger import log

from tags import TextTag, EndTag


class Widget(element.Element):
	pass

class Text(Widget):
	def __init__(self, text):
		super(Text, self).__init__()
		self.register_event_types('on_edit')
		self.color = (150,150,255,255)
		self.text = text
		
	def get_caret_position(self):
		return self.doc.caret_position - self.doc.positions[self]
		
	def render(self):
		return [TextTag(self.text)]
	
	def on_text(self, text):
		pos = self.get_caret_position()
		log(pos)

		self.text = self.text[:pos] + text + self.text[pos:]

		self.post_render_move_caret = len(text)
		
		log(self.text + "len: " + len(self.text))
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

	def __init__(self, text, shadow):

		super(ShadowedText, self).__init__(text)
		self.shadow = shadow

	def render(self):
		return [TextTag(self.text),
				ColorTag((130,130,130,255)),
				TextTag(self.shadow[len(self.text):])]

	def len(self):
		return len(self.text+self.shadow[len(self.text)])
		


class Menu(Widget):
	def __init__(self, items):
		super(Menu, self).__init__()
		[self.register_event_type(i) for i in ['on_click']]
		self.color = (100,230,50,255)
		self.items = items
		self.sel = -1

	def render(self):
		for i, item in enumerate(self.items):
			#we will need to shift this here
			self.doc.append("\n", self)
			self.doc.append(item, self, 
				{'color':(255,100,100,255)} if self.sel == i else {})

		self.doc.append("\n", self)
		
	




class Button(Widget):
	def __init__(self, text="[🔳🔳🔳🔳]"):
		super(Button, self).__init__()
		self.register_event_types('on_click, on_text')
		self.color = (255,150,150,255)
		self.text = text
	def on_mouse_press(self, x, y, button, modifiers):
		ping()
		self.dispatch_event('on_click', self)
	def on_text(self, text):
		ping()
		if text == "\r":
			self.dispatch_event('on_click', self)
		else:
			self.dispatch_event('on_text',  text)
		
	def render(self):
		return TextTag(self.text)

class Number(Text):
	"""Number widget inherits from text, contents are only int()'ed when needed"""	
	def __init__(self, text):
		super(Number, self).__init__(text)
		self.text = str(text)
		self.set('minus_button', Button("-"))
		self.set('plus_button', Button("+"))
		self.minus_button.push_handlers(on_click=self.on_widget_click, on_text=self.on_widget_text)
		self.plus_button.push_handlers(on_click=self.on_widget_click, on_text=self.on_widget_text)
	def render(self):
		return self.minus_button.tags()+TextTag(self.text)+self.plus_button.tags()
	@property
	def value(self):
		return int(self.text)
	def inc(self):
		self.text = str(int(self.text)+1)
	def dec(self):
		self.text = str(int(self.text)-1)

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
				
class Toggle(Widget):
	def __init__(self, value):
		super(Toggle, self).__init__()
		self.value = value
	def render(self):
		return TextTag(self.text)
	@property
	def text(self):
		return "checked" if self.value else "unchecked"
	def on_mouse_press(self, x, y, button, modifiers):
		self.value = not self.value
		self.dispatch_event('on_edit', self)
		


