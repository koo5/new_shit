
from pygame import gfxdraw, font

import nodes
import color


class Menu(object):
	def __init__(self, tag, x, y):
		self.items = [Item(self, i) for i in tag.items]
		
	def draw(self, surf, rect):
		s = pygame.Surface(rect, SRCALPHA, screen_surface)

		self.fg = (255,255,255,255)
		self.bg = (0,0,0,100)

		x,y,w,h = rect

		for item in self.items:
			sur = item.render(self)
			s.blit(sur,(x,y))
			y += s.get_height()
		return s

class Item(object):
	def __init__(self, menu, value):
		self.menu = menu
		self.value = value
		if isinstance(value, nodes.TypeDeclaration):
			self.text = str(value.type)
		else:raise hell
		
	def render(self)
		font.render(self.text, True, self.menu.fg, self.menu.bg)
				s.blit(sur,(x,y))
	
	
