from colors import colors
import project
import typed
import menu



def change_font_size():
	global font, font_width, font_height
	font = pygame.font.SysFont('monospace', args.font_size)
	font_width, font_height = font.size("X")


class Frame(object):
#	def on_mouse_press(self, e):
#	def keypress(self, e):
#	def draw(self):

	@property
	def pos(self):
		return (self.width, self.height)

def xy2cr((x, y)):
	c = x / font_width
	r = y / font_height
	return c, r


class Root(Frame):
	def __init__(self, size):
		self.cursor_c = self.cursor_r = 0
		self.root = typed.make_root()
		self.root.fix_parents()
		self.scroll_lines = 0
		self.size = size

	def under_cr(self, (c, r)):
		try:
			return self.lines[r][c][1]["node"]
		except:
			return None

	def under_cursor(self):
		return self.under_cr((self.cursor_c, self.cursor_r))

	def first_nonblank(self):
		r = 0
		for ch, a in self.lines[self.cursor_r]:
			if ch in [" ", u" "]:
				r += 1
			else:
				return r

	def element_char_index(self):
		try:
			return self.lines[self.cursor_r][self.cursor_c][1]["char_index"]
		except:
			return None

	def move_cursor_h(s, x):
		"""returns True if it moved"""
		old = s.cursor_c, s.cursor_r
		s.cursor_c += x
		if s.cursor_c > len(s.lines[s.cursor_r]):
			s.move_cursor_v(1)
			s.cursor_c = 0
		if s.cursor_c < 0: s.cursor_c = 0
		return old = s.cursor_c, s.cursor_r

	def move_cursor_v(self, count):
		r = self.cursor_r + count
		sl = self.scroll_lines
		if r > self.rows:
			sl += r - self.rows
			r = self.rows
		if r < 0:
			sl += r
			r = 0
			if sl < 0:
				sl = 0
		self.cursor_r = r
		self.scroll_lines = sl

	@property
	def rows(self):
		return self.height / font_height

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

	def generate_arrows(self):
		self.arrows = []
		if not arrows_visible: return

		for r,l in enumerate(self.lines):
			for c,i in enumerate(l):
				if i[1].has_key("arrow"):
					target = project.find(i[1]["arrow"], self.lines)
					if target:
						arrows.append(((c,r),target))

	def draw_lines(self):
		s = pygame.Surface(self.size)
		s.fill(colors.bg)
		uc = self.under_cursor()
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
		#todo: real arrows would be cool
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


	def prev_elem(s):
		e = s.under_cursor()
		while s.move_cursor_h(-1):
			if e != s.under_cursor():
				break

	def next_elem(s):
		e = s.under_cursor()
		while s.move_cursor_h(1):
			if e != s.under_cursor():
				break

	def top_keypress(s, event):

		k = event.key

		if pygame.KMOD_CTRL & event.mod:
			elif k == pygame.K_LEFT:
				s.prev_elem()
			elif k == pygame.K_RIGHT:
				s.next_elem()
			else:
				return False
		else:
			"""if k == pygame.K_F12:
				for item in root.flatten():
					if isinstance(item, typed.Syntaxed):
						item.view_normalized = not item.view_normalized
			el"""
			elif k == pygame.K_F8:
				toggle_arrows()
			elif k == pygame.K_F5:
				run()
			elif k == pygame.K_UP:
				s.move_cursor_v(-1)
				s.and_sides(event)
			elif k == pygame.K_DOWN:
				s.move_cursor.v(+1)
				s.and_sides(event)
			elif k == pygame.K_LEFT:
				move_cursor(-1)
				and_updown(event)
			elif k == pygame.K_RIGHT:
				move_cursor(+1)
				and_updown(event)
			elif k == pygame.K_HOME:
				if cursor_c != 0:
					cursor_c = 0
				else:
					cursor_c = first_nonblank()
			elif k == pygame.K_END:
				cursor_c = len(lines[cursor_r])
			elif k == pygame.K_PAGEUP:
				updown_cursor(-10)
			elif k == pygame.K_PAGEDOWN:
				updown_cursor(10)

			else:
				return False
		return True


def keypress(self, event):
	event = KeypressEvent(event, self.element_char_index(), (self.cursor_c, self.cursor_r)))
	element = self.under_cursor()
	while element != None and not element.on_keypress(event):
		element = element.parent
	if element != None:#some element handled it
		self.move_cursor(root.post_render_move_caret)
		root.post_render_move_caret = 0
		return




class Menu(Frame):
	def __init__(self, size):
		self.scroll = 0
		self.sel = 0
		self._items = []

	@property
	def items(self):
		return self._items

	@items.setter
	def items(self, value):
		if self.sel > len(value) - 1:
			self.sel = len(value) - 1
		self._items = value

	def render():
		self.lines = []
		for i in self.items[self.scroll:self.scroll + self.rows]:
			self.lines.extend(project.project(i, self.cols)

	def draw(self):
		self.render()
		s = self.draw_lines()
		self.draw_rects(s)
		return s

	def draw_rects(self, s):
		for i in self.root.items:
			startline = i._render_lines[0]["line"]
			endline = i._render_lines[-1]["line"]
			startchar = min([c["start"] for c in i._render_lines)
			endchar   = max([c["end"] for c in i._render_lines)





def update_menu():
	e = under_cursor()
	menu.element = e
	new_items = []
	while e != None:
		new_items += e.menu()
		e = e.parent
	new_items += menu.help()
	new_items += top_help()
	if valid_only:
		new_items = [x for x in new_items if x.valid]
	menu.items = new_items

