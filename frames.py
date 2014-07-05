import pygame
from pygame import draw

from colors import color, colors
import project
import typed
from tags import TextTag, ElementTag, WidgetTag, ColorTag, EndTag
from menu_items import InfoItem
import widgets

font = font_height = font_width = 666



class Frame(object):
#	def on_mouse_press(self, e):
#	def on_keypress(self, e):
#	def draw(self):

	def draw_lines(self): #we didnt start the fire...
		s = pygame.Surface((self.rect.w, self.rect.h))
		s.fill(colors.bg)
		for row, line in enumerate(self.lines):
			for col, char in enumerate(line):
				x = font_width * col
				y = font_height * row
				fg = color(char[1]['color'])
				bg = color("bg")
				sur = font.render(
					char[0],True,
					fg,
					bg)
				s.blit(sur,(x,y))
		return s

	def under_cr(self, (c, r)):
		try:
			return self.lines[r][c][1]["node"]
		except:
			return None

	def mousedown(s,e,pos):
		#	log(e.button)
		n = s.under_cr(xy2cr(pos))
		if n:
			n.on_mouse_press(e.button)

	def __init__(s):
		s.rect = pygame.Rect((6,6,6,6))
		s.lines = []

	@property
	def items_on_screen(s):
		return s.items[s.scroll:s.scroll + s.rows]

	def render(s):
		r = []
		for i in s.items_on_screen:
			r += [ElementTag(i), "\n"]
		s.lines = project.project_tags(r, s.cols, s).lines

	@property
	def rows(self):
		return self.rect.h / font_height


	@property
	def cols(self):
		return self.rect.w / font_width


def xy2cr((x, y)):
	c = x / font_width
	r = y / font_height
	return c, r


class Root(Frame):
	def __init__(self):
		super(Root, self).__init__()
		self.cursor_c = self.cursor_r = 0
		self.root = typed.make_root()
		self.root.fix_parents()
		self.scroll_lines = 0
		self.arrows_visible = True

	def and_sides(s,e):
		if e.all[pygame.K_LEFT]: s.move_cursor_h(-1)
		if e.all[pygame.K_RIGHT]: s.move_cursor_h(1)

	def and_updown(s,event):
		if event.all[pygame.K_UP]: s.move_cursor_v(-1)
		if event.all[pygame.K_DOWN]: s.move_cursor_v(1)

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
		return self.atts["char_index"]

	@property
	def atts(self):
		try:
			return self.lines[self.cursor_r][self.cursor_c][1]
		except IndexError:
			return None

	def move_cursor_h(s, x):
		"""returns True if it moved"""
		old = s.cursor_c, s.cursor_r
		s.cursor_c += x
		if s.cursor_c > len(s.lines[s.cursor_r]):
			s.move_cursor_v(1)
			s.cursor_c = 0
		if s.cursor_c < 0:
			#todo
			s.cursor_c = 0
		return old != (s.cursor_c, s.cursor_r)

	def move_cursor_v(self, count):
		r = self.cursor_r + count
		sl = self.scroll_lines
		if r >= self.rows:
			sl += r - self.rows +1
			r = self.rows-1
		if r < 0:
			sl += r
			r = 0
			if sl < 0:
				sl = 0
		self.cursor_r = r
		self.scroll_lines = sl


	def render(self):

		p = project.project(self.root, self.cols, self)
		self.lines = p.lines[self.scroll_lines:self.scroll_lines + self.rows]
		self.arrows = p.arrows

		if __debug__:
			assert(isinstance(self.lines, list))
			for l in self.lines:
				assert(isinstance(l, list))
				for i in l:
					assert(isinstance(i, tuple))
					assert(isinstance(i[0], str) or isinstance(i[0], unicode))
					assert(len(i[0]) == 1)
					assert(isinstance(i[1], dict))
					assert(i[1]['node'])
					assert(i[1].has_key('char_index'))

	def generate_arrows(self):
		if not self.arrows_visible:
			self.arrows = []
			return
		r = []
		for a in self.arrows:
			target = project.find(a[2], self.lines)
			if target:
				r.append(((a[0],a[1]),target))
		self.arrows = r

	def draw_lines(self, surf):
		uc = self.under_cursor()
		for row, line in enumerate(self.lines):
			for col, char in enumerate(line):
				x = font_width * col
				y = font_height * row
				fg = color(char[1]['color'])
				bg = color("bg" if not char[1]['node'] == uc else "highlighted bg")
				sur = font.render(
					char[0],
					1,
					fg
					)
				surf.blit(sur,(x,y))

	def draw_arrows(s, surface):
		#todo: real arrows would be cool
		for ((c,r),(c2,r2)) in s.arrows:
			x,y,x2,y2 = font_width * (c+0.5), font_height * (r+0.5), font_width * (c2+0.5), font_height * (r2+0.5)
			pygame.draw.line(surface, color("arrow"), (x,y),(x2,y2))

	def draw(self):
		self.render()
		self.generate_arrows()
		surf = pygame.Surface((self.rect.w, self.rect.h), 0, pygame.display.get_surface())
		#surf.fill(colors.bg)
		self.draw_arrows(surf)
		self.draw_lines(surf)
		self.draw_cursor(surf)
		return surf

	def draw_cursor(self, s):
		x, y, y2 = self.cursor_xy()
		pygame.draw.rect(s, colors.cursor,
						 (x, y, 1, y2 - y,))

	def cursor_xy(s):
		return (font_width * s.cursor_c,
		        font_height * s.cursor_r,
		        font_height * (s.cursor_r + 1))


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

	def cursor_home(s):
		if s.cursor_c != 0:
			s.cursor_c = 0
		else:
			s.cursor_c = s.first_nonblank()

	def cursor_end(s):
		s.cursor_c = len(s.lines[s.cursor_r])

	def run(s):
		s.root['program'].run()

	def top_keypress(s, event):

		k = event.key

		if pygame.KMOD_CTRL & event.mod:
			if k == pygame.K_LEFT:
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
			if k == pygame.K_F8:
				s.toggle_arrows()
			elif k == pygame.K_F5:
				s.run()
			elif k == pygame.K_UP:
				s.move_cursor_v(-1)
				s.and_sides(event)
			elif k == pygame.K_DOWN:
				s.move_cursor_v(+1)
				s.and_sides(event)
			elif k == pygame.K_LEFT:
				s.move_cursor_h(-1)
				s.and_updown(event)
			elif k == pygame.K_RIGHT:
				s.move_cursor_h(+1)
				s.and_updown(event)
			elif k == pygame.K_HOME:
				s.cursor_home()
			elif k == pygame.K_END:
				s.cursor_end()
			elif k == pygame.K_PAGEUP:
				s.move_cursor_v(-10)
			elif k == pygame.K_PAGEDOWN:
				s.move_cursor_v(10)
			else:
				return False
		return True


	def on_keypress(self, event):
		event.frame = self
		event.cursor = (self.cursor_c, self.cursor_r)
		event.atts = self.atts
		if self.top_keypress(event):
			return True
		element = self.under_cursor()
		while element != None and not element.on_keypress(event):
			element = element.parent
		if element != None:#some element handled it
			self.move_cursor_h(self.root.post_render_move_caret)
			self.root.post_render_move_caret = 0
			return True


class Menu(Frame):
	def __init__(s):
		super(Menu, s).__init__()
		s.scroll = 0
		s.sel = 0
		s._items = []
		s.valid_only = False

	@property
	def items(self):
		return self._items

	@property
	def selected(self):
		return self.items[self.sel]

	@items.setter
	def items(self, value):
		if self.sel > len(value) - 1:
			self.sel = len(value) - 1
		if self.sel < 0:
			self.sel = 0
		self._items = value

	def draw(s):
		surface = s.draw_lines()
		s.draw_rects(surface)
		return surface

	def draw_rects(s, surface):
		for i in s.items_on_screen:
			rl = i._render_lines[s]
			#print rl
			startline = rl["startline"]
			endline = rl["endline"]
			startchar = 0
			endchar = max([len(l) for l in s.lines[startline:endline+1]])
			r = pygame.Rect(startchar * font_width,
			                startline * font_height,
			                (endchar  - startchar) * font_width,
			                (endline - startline+1) * font_height)
			if i == s.selected:
				c = colors.menu_rect_selected
			else:
				c = colors.menu_rect
			draw.rect(surface, c, r, 1)

	def update(s, root):
		e = root.under_cursor()
		atts = root.atts
		s.element = e
		new_items = []
		while e != None:
			new_items += e.menu(atts)
			e = e.parent
		if s.valid_only:
			new_items = [x for x in new_items if x.valid]
		s.items = new_items


	def on_keypress(self, e):
		if e.mod & pygame.KMOD_CTRL:
			if e.key == pygame.K_UP:
				self.move(-1)
				return True
			if e.key == pygame.K_DOWN:
				self.move(1)
				return True
		if e.key == pygame.K_SPACE:
			self.element.menu_item_selected(self.items[self.sel], self.root.atts)
			self.sel = 0
			return True

	def mousedown(s,e,pos):
		n = s.under_cr(xy2cr(pos))
		if n:
			s.element.menu_item_selected(n, None)

	def move(self, y):
		self.sel += y
		if self.sel < 0: self.sel = 0
		if self.sel >= len(self.items): self.sel = len(self.items) - 1
		#print len(self.items), self.sel


	def toggle_valid(s):
		s.valid_only = not s.valid_only


class Info(Frame):

	def __init__(s):
		super(Info, s).__init__()
		s.top_info = [InfoItem(t) for t in [
			"ctrl + =,- : font size",
			"f9 : only valid items in menu",
			"f8 : arrows",
			"f5 : eval",
			"ctrl + up, down: menu movement",
			"space: menu selection",
			"",
			"[text] are textboxes",
			"orange <>'s are Compiler",
			"red <>'s enclose nodes or other widgets",
			"(gray)'s are the type the compiler expects",
			"currently you can only insert nodes manually by selecting them from the menu, with prolog, the compiler will start guessing what you mean:)"
		]]
		#,	"f12 : normalize syntaxes"
		s.hierarchy_infoitem = InfoItem("bla")
		s.hidden_toggle = widgets.Toggle(s, True, ("(.....)", "(...)"))
		s.hidden_toggle.color = s.hidden_toggle.brackets_color = "info item visibility toggle"

	@property
	def used_height(s):
		return len(s.lines) * font_height

	def update(s):
		s.items = s.top_info[:]
		s.items.append(s.hierarchy_infoitem)
		#elements..

	def render(s):
		s.update()
		r = [ColorTag("help"), TextTag("help:  "), ElementTag(s.hidden_toggle), "\n"]
		for i in s.items:
			if not s.hidden_toggle.value or i.visibility_toggle.value:
				r += [ElementTag(i), "\n"]
		r += [EndTag()]
		s.lines = project.project_tags(r, s.cols, s).lines

	def draw(s):
		surface = s.draw_lines()
		return surface


#todo: definition / insight frame? preferably able to float in multiple numbers around the code in root
#status / log window
#toolbar (toolbar.py)
#settings, the doc?
