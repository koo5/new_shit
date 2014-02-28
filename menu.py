
import nodes
import colors
from logger import ping,log

class Menu(object):
	def __init__(self, tag):
		self.items = [Item(self, i) for i in tag.items]
		
	def draw(self, scr, font, x, y, size):
#		s = pygame.Surface((self.rect, pygame.SRCALPHA)
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
		
	def render(self, scr, font, x, y):
		s = font.render("["+self.text, True, self.menu.fg, self.menu.bg)
		scr.blit(s,(x,y))
		return s.get_height()
	
	
