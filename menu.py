import pygame

#import nodes
import colors
from logger import ping,log

class Menu(object):
	def __init__(self):
		self.sel = 0
		self.items = [MenuItem("hello", 5)]
		
	def draw(self, scr, font, x, y, size):
		#s = pygame.Surface((size[0], size[1]), pygame.SRCALPHA)
		self.fg = (255,255,255,255)
		self.bg = (0,0,0,100)
		
		for item in self.items:
			assert(isinstance(item, MenuItem))
			h = item.render(self, scr, font, x, y)
			y += h
			
	def keypress(e):
		pass

class MenuItem(object):
	def __init__(self, text, value):
		self.text = text
		self.value = value
#		if isinstance(value, nodes.TypeDeclaration):
#			self.text = str(value.type)
#		else:raise hell
		
	def render(self, menu, s, font, x, y):
		fs = font.render(self.text, True, menu.fg, menu.bg)
		s.blit(fs,(x,y))
		#print self.text
		return fs.get_height()
	
	
