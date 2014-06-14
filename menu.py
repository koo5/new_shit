import pygame


import colors
from logger import ping
from element import Element
import widgets
from tags import *


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

	def draw(self, scr, font, x, y, size):
		#s = pygame.Surface((size[0], size[1]), pygame.SRCALPHA)
		menu_area = pygame.Rect(0,0,0,0)
		ypos = y
		for i, item in enumerate(self.items):
			#log(str(item))
			assert(isinstance(item, MenuItem))
			item_area = item.draw(self, scr, font, x, ypos)
			item.rect = (x,ypos, item_area.w, item_area.h)
			if i == self.sel:
				pygame.draw.rect(scr, colors.fg, (x, ypos, item_area.w, item_area.h), 1)
			else:
				pygame.draw.rect(scr, (0,0,200), (x, ypos, item_area.w, item_area.h), 1)
			menu_area = menu_area.union((0, ypos, item_area.w, item_area.h))
			ypos += item_area.h
			if ypos > size[1]:
				break
			#print area.h
		#pygame.draw.rect(scr, (100,100,100), (x,y,menu_area.w,menu_area.h), 1)
	
	def help(self):
		return [HelpMenuItem(t) for t in [
		"ctrl + up, down: menu movement",
		"space: menu selection"]]

	
	
	def keypress(self, e):
#		ping()
		if e.mod & pygame.KMOD_CTRL:
			if e.key == pygame.K_UP:
				self.move(-1)
				return True
			if e.key == pygame.K_DOWN:
				self.move(1)
				return True
		if e.key == pygame.K_SPACE:
#			print self.sel
#			log(self.items[self.sel])
			self.element.menu_item_selected(self.items[self.sel], None)
			self.sel = 0
			return True
				

	def move(self,y):
		ping()
		self.sel += y
		if self.sel < 0: self.sel = 0
		if self.sel >= len(self.items): self.sel = len(self.items) - 1
		print len(self.items), self.sel

#on mousedown or (mousemove if mouse is down):
#	self.sel = item under mouse


class HelpMenu(Menu):


    def render(self):
        r = [TextTag("help  "), ColorTag((100,100,100)), WidgetTag(visible_toggle), EndTag()]
        for i in self.items:
            if not self.hidden_toggle.value or i.visible_toggle.value:
                r += i.render()


class MenuItem(Element):
	def __init__(self):
        superMenuItem, self).__init__()
		self.brackets = ('<','>')


class HelpMenuItem(MenuItem):
	def __init__(self, text):
		super(HelpMenuItem, self).__init__()
		self.text = text
		self.color = (255,255,255)
        self.visible_toggle = widgets.Toggle(self, True, ("(X)", "show"))
        self.visible_toggle.push_handlers(on_change = self.visible_toggle_onclick)
        self.visible_toggle.color = (100,100,100)

    def render(self):
        return [TextTag(self.text + "  "), WidgetTag(self.visible_toggle)]


class InfoMenuItem(MenuItem):
	def __init__(self, text):
		super(InfoMenuItem, self).__init__()
		self.text = "(" + text + ")"
		self.color = (200,200,200)
