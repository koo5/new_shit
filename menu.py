import pygame

import nodes
import colors
from logger import ping,log

class Menu(object):
	def __init__(self, tag):
		self.items = [Item(self, i) for i in tag.items]
		
	def draw(self, scr, font, x, y, size):
		#s = pygame.Surface((size[0], size[1]), pygame.SRCALPHA)
		self.fg = (255,255,255,255)
		self.bg = (0,0,0,100)
		
		for item in self.items:
			h = item.render(scr, font, x, y)
			y += h
			
	def keypress(e):
		pass		

class Item(object):
	def __init__(self, menu, value):
		self.menu = menu
		self.value = value
		if isinstance(value, nodes.TypeDeclaration):
			self.text = str(value.type)
		else:raise hell
		
	def render(self, s, font, x, y):
		fs = font.render("["+self.text, True, self.menu.fg, self.menu.bg)
		s.blit(fs,(x,y))
		return fs.get_height()
	
	
