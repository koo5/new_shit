import pygame


import colors
from logger import ping
from element import Element
import widgets
from tags import *
from menu_items import *

class Menu(Element):
	def __init__(self):
		super(Menu, self).__init__()
		self.sel = 0
		self._items = [InfoMenuItem("hello")]
		self.active_element = None

	@property
	def items(self):
		return self._items
	@items.setter
	def items(self, value):
		if self.sel > len(value) - 1:
			self.sel = len(value) - 1
		self._items = value

			if i == self.sel:
				pygame.draw.rect(scr, colors.fg, (x, ypos, item_area.w, item_area.h), 1)
			else:
				pygame.draw.rect(scr, (0,0,200), (x, ypos, item_area.w, item_area.h), 1)
			menu_area = menu_area.union((0, ypos, item_area.w, item_area.h))
			ypos += item_area.h
			if ypos > size[1]:
				break

	
	



"""
#on mousedown or (mousemove if mouse is down):
	(c,r):
		translate row by scroll
		for i in self.items:
			if i._render_start_line <= r and i._render_end_line >= r
#	self.sel = item under mouse
"""

class InfoMenu(Menu):
	def render(self):
		r = [TextTag("info  "), ColorTag((100,100,100)), WidgetTag(visible_toggle), EndTag()]
		for i in self.items:
			if not self.hidden_toggle.value or i.visible_toggle.value:
				r += i.render()
		return r

