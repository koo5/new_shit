from colors import colors
import project
import typed
import menu



def change_font_size():
	global font, font_width, font_height
	font = pygame.font.SysFont('monospace', args.font_size)
	font_width, font_height = font.size("X")


class Frame(object):
	def on_mouse_press(self, e):


	def keypress(self, e):


	def draw(self):



class Root(Frame):
	def __init__(self, size):
		self.cursor_c = self.cursor_r = 0
		self.root = typed.make_root()
		self.root.fix_parents()
		self.scroll_lines = 0
		self.size = size

	@property
	def rows(self):
		return self.size[1] / font_height

	def render():
		self.arrows = []
		lines = project.project(self.root, self.size[0])
		self.lines = lines[self.scroll_lines:self.scroll_lines + self.rows]

		if __debug__:
			assert(isinstance(self.lines, list))
			for l in lines:
				assert(isinstance(l, list))
				for i in l:
					assert(isinstance(i, tuple))
					assert(isinstance(i[0], str) or isinstance(i[0], unicode))
					assert(len(i[0]) == 1)
					assert(isinstance(i[1], dict))
					assert(i[1]['node'])
					assert(i[1].has_key('char_index'))

	def generate_arrows():
		self.arrows = []
		if not arrows_visible: return

		for r,l in enumerate(self.lines):
			for c,i in enumerate(l):
				if i[1].has_key("arrow"):
					target = project.find(i[1]["arrow"], self.lines)
					if target:
						arrows.append(((c,r),target))

	def draw(self):
		s = pygame.Surface(self.size)
		s.fill(colors.bg)
		uc = under_cursor()
		for row, line in enumerate(self.lines):
			for col, char in enumerate(line):
				x = font_width * col
				y = font_height * row
				sur = font.render(
					char[0],True,
					colors[char[1]['color']],
					colors["bg"] if not char[1]['node'] == uc else (40,0,0)) #highlight element under cursor
				s.blit(sur,(x,y))
		return s

	def draw_arrows(sself, ur):
		for ((c,r),(c2,r2)) in self.arrows:
			x,y,x2,y2 = font_width * (c+0.5), font_height * (r+0.5), font_width * (c2+0.5), font_height * (r2+0.5)
			pygame.draw.line(sur, (55,55,55), (x,y),(x2,y2))

	def draw(self):
		self.render()
		self.generate_arrows()
		s = self.draw()
		draw_arrows(s)
		self.draw_cursor(s)
		return s

	def draw_cursor(self, s):
		x, y, y2 = cursor_xy()
		pygame.draw.rect(s, colors.cursor,
						 (x, y, 1, y2 - y,))



class Menu(Frame):
	def __init__(self, size):
		self.root = menu.Menu()
		self.scroll_lines = 0
		self.size = size

	def render():
		self.arrows = []
		lines = project.project(self.root, self.size[0])


	def draw(self):
		self.render()
		s = self.draw()
		self.draw_rects(s)
		return s

	def under_cursor(self):
		return None

	def draw_rects(self, s):
		for i in self.root.items:
			startline = i._render_lines[0]["line"]
			endline = i._render_lines[-1]["line"]
			startchar = min([c["start"] for c in i._render_lines)
			endchar   = max([c["end"],




