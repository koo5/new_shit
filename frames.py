import pygame
from pygame import draw
from math import *

from colors import color, colors
import project
import nodes
from tags import TextTag, ElementTag, WidgetTag, ColorTag, EndTag
from menu_items import InfoItem
import widgets
from logger import log

font = font_height = font_width = 666

#gotta refactor stuff common to Menu and Info to some SimpleFrame or something

class Frame(object):
#	def on_mouse_press(self, e):
#	def on_keypress(self, e):
#	def draw(self):

	def __init__(s):
		s.rect = pygame.Rect((6,6,6,6))
		s.lines = []
		s.scroll_lines = 0
		s._render_lines = {}#hack

	def project(s):
		s.lines = project.project(s,
		    s.cols, s, s.scroll_lines + s.rows).lines[s.scroll_lines:]

	def draw(self):
		surface = pygame.Surface((self.rect.w, self.rect.h), 0)#, pygame.display.get_surface())
		if colors.bg != (0,0,0):
			surface.fill(colors.bg)
		self._draw(surface)
		return surface

	def draw_lines(self, surf, highlight=None, transparent=False):
		for row, line in enumerate(self.lines):
			for col, char in enumerate(line):
				x = font_width * col
				y = font_height * row
				fg = color(char[1]['color'])
				bg = color("highlighted bg" if (
					'node' in char[1] and
					char[1]['node'] == highlight and
					not args.eightbit) else "bg")
				if transparent:
					sur = font.render(char[0],1,fg)
				else:#its either arrows or highlighting, you cant have everything, hehe
					sur = font.render(char[0],1,fg,bg)
				surf.blit(sur,(x,y))


	def under_cr(self, (c, r)):
		try:
			return self.lines[r][c][1]["node"]
		except:
			return None

	def click(s,e,pos):
		cr = xy2cr(pos) #cursor column, row
		n = s.under_cr(cr)
		if log_events:
			log(str(e) + " on " + str(n))
		if not n or not n.on_mouse_press(e.button):
			s.cursor_c, s.cursor_r = cr

	def mousedown(s,e,pos):
		if e.button == 1:
			s.click(e,pos)
		elif e.button == 4:
			s.scroll(-1)
		elif e.button == 5:
			s.scroll(1)

	def scroll(s,l):
		s.scroll_lines += l
		if s.scroll_lines < 0:
			s.scroll_lines = 0

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
		self.root = nodes.make_root()
		self.root.fix_parents()
		self.arrows_visible = True
		self.cursor_blink_phase = True
		self.menu_dirty = True

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
		old = s.cursor_c, s.cursor_r, s.scroll_lines
		s.cursor_c += x
		if len(s.lines) <= s.cursor_r or s.cursor_c > len(s.lines[s.cursor_r]):
			s.move_cursor_v(x)
			s.cursor_c = 0
		if s.cursor_c < 0:
			if s.move_cursor_v(-1):
				s.cursor_c = len(s.lines[s.cursor_r])
		return old != (s.cursor_c, s.cursor_r, s.scroll_lines)

	def move_cursor_v(s, count):
		"""returns True if it moved. atm, screen bottom is unlimited"""
		old = s.cursor_c, s.cursor_r, s.scroll_lines
		r = s.cursor_r + count
		sl = s.scroll_lines
		if r >= s.rows:
			sl += r - s.rows +1
			r = s.rows-1
		if r < 0:
			sl += r
			r = 0
			if sl < 0:
				sl = 0
		s.cursor_r = r
		s.scroll_lines = sl
		return old != (s.cursor_c, s.cursor_r, s.scroll_lines)

	def render(self):
		p = project.project(self.root, self.cols, self, self.scroll_lines + self.rows)
		self.lines = p.lines[self.scroll_lines:]
		self.arrows = self.complete_arrows(p.arrows)
		self.do_post_render_move_caret()

		if __debug__:  #todo: __debug__projection__ or something, this is eating quite some cpu i think and only checks the projection code (i think)
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

	#todo: clean this up ugh, oh and arrows are broken, the source point stays stuck when you scoll
	def complete_arrows(self, arrows):
		if not self.arrows_visible:
			return []
		r = []
		for a in arrows:
			target = project.find(a[2], self.lines)
			if target:
				r.append(((a[0],a[1] - self.scroll_lines),target))
		return r

	def draw_arrows(s, surface):
		#todo: real arrows would be cool
		for ((c,r),(c2,r2)) in s.arrows:
			#print c,r,c2,r2
			x,y,x2,y2 = font_width * (c+0.5), font_height * (r+0.5), font_width * (c2+0.5), font_height * (r2+0.5)
			pygame.draw.line(surface, color("arrow"), (x,y),(x2,y2))
			mmm = 20
			aaa = 0.2
			a = \
				atan2(y-y2, x-x2)
			ll = mmm * cos(a+aaa) + x2, mmm * sin(a+aaa) + y2
			pygame.draw.line(surface, color("arrow"), ll,(x2,y2))
			ll = mmm * cos(a-aaa) + x2, mmm * sin(a-aaa) + y2
			pygame.draw.line(surface, color("arrow"), ll,(x2,y2))


	def _draw(self, surf):
		self.draw_arrows(surf)
		self.draw_lines(surf, self.under_cursor(), self.arrows_visible)
		self.draw_cursor(surf)

	def draw_cursor(self, s):
		if self.cursor_blink_phase:
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

	def cursor_top(s):
		s.cursor_r = 0

	def cursor_bottom(s):
		log("hmpf")

	def run(s):
		s.root['program'].run()

	def run_line(s):
		s.root['program'].run_line(s.under_cursor())

	def clear(s):
		s.root['program'].clear()

	def toggle_arrows(s):
		s.arrows_visible = not s.arrows_visible

	def top_keypress(s, event):

		k = event.key

		if pygame.KMOD_CTRL & event.mod:
			if k == pygame.K_LEFT:
				s.prev_elem()
			elif k == pygame.K_RIGHT:
				s.next_elem()
			elif k == pygame.K_HOME:
				s.cursor_top()
			elif k == pygame.K_END:
				s.cursor_bottom()
			elif k == pygame.K_q:
				#a quit shortcut that goes thru the event pickle/replay mechanism
				exit()
			else:
				return False
		else:
			"""if k == pygame.K_F12:
				for item in root.flatten():
					if isinstance(item, nodes.Syntaxed):
						item.view_normalized = not item.view_normalized
			el"""

			if k == pygame.K_F4:
				s.clear()
			elif k == pygame.K_F5:
				s.run()
			elif k == pygame.K_F6:
				s.run_line()
			elif k == pygame.K_F8:
				s.toggle_arrows()
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
			if log_events:
				log("handled by root frame")
			return True
		element = self.under_cursor()

		#new style handlers
		if element != None and element.dispatch_levent(event):
			return True

		while element != None and not element.on_keypress(event):
			element = element.parent
		if element != None:#some element handled it
			if log_events:
				log("handled by "+str(element))
			return True

	def do_post_render_move_caret(s):
		if isinstance(s.root.post_render_move_caret, int):
			s.move_cursor_h(s.root.post_render_move_caret)
		else: #its a node
			log(s.root.post_render_move_caret)
			s.cursor_c, s.cursor_r = project.find(s.root.post_render_move_caret, s.lines)
		s.root.post_render_move_caret = 0


class Menu(Frame):
	def __init__(s):
		super(Menu, s).__init__()
		s.sel = 0
		#index to items_on_screen. not ideal.
		#todo: a separate wishedfor_sel
		s.valid_only = False

	@property
	def selected(s):
		return s.items_on_screen[s.sel]

	def clamp_sel(s):
		if s.sel >= len(s.items_on_screen):
			s.sel = len(s.items_on_screen) - 1
		if s.sel < 0:
			s.sel = 0

	def _draw(s, surface):
		s.draw_lines(surface)
		s.draw_rects(surface)

	def generate_rects(s):
		s.rects = dict()
		for i in s.items_on_screen:
			rl = i._render_lines[s]

			startline = rl["startline"] - s.scroll_lines if "startline" in rl else 0
			endline = rl["endline"]  - s.scroll_lines if "endline" in rl else s.rows

			if endline < 0 or startline > s.rows:
				continue
			if startline < 0:
				startline = 0
			if endline > s.rows - 1:
				endline = s.rows - 1

			startchar = 0
			print startline, endline+1
			endchar = max([len(l) for l in s.lines[startline:endline+1]])
			r = pygame.Rect(startchar * font_width,
			                startline * font_height,
			                (endchar  - startchar) * font_width,
			                (endline - startline+1) * font_height)
			s.rects[i] = r

	def draw_rects(s, surface):
		for i,r in s.rects.iteritems():
			if i == s.selected:
				c = colors.menu_rect_selected
			else:
				c = colors.menu_rect
			draw.rect(surface, c, r, 1)

	def render(s, root):
		s.root_frame = root
		s.project()
		s.clamp_sel()
		s.generate_rects()

	def tags(s):
		s.items_on_screen = []
		yield ColorTag("fg")
		for i in s.generate_palette():
			s.items_on_screen.append(i)
			yield [ElementTag(i), "\n"]
		yield EndTag()

	def generate_palette(s):
		e = s.root_frame.under_cursor()
		atts = s.root_frame.atts
		if e != None:
			for i in e.menu(atts):
				if not s.valid_only or i.valid:
					yield i

	def on_keypress(self, e):
		if e.mod & pygame.KMOD_CTRL:
			if e.key == pygame.K_UP:
				self.move(-1)
				return True
			if e.key == pygame.K_DOWN:
				self.move(1)
				return True
		if e.key == pygame.K_SPACE:
			return self.accept()

	def click(s,e,pos):
		for i,r in s.rects.iteritems():
			if r.collidepoint(pos):
				s.sel = s.items_on_screen.index(i)
				s.accept()

	def accept(self):
		if (self.sel < len(self.items) and
				self.element.menu_item_selected(self.items[self.sel], self.root.atts)):
			self.sel = 0
			return True


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
		#create all infoitems at __init__, makes persistence possible (for visibility state)
		s.top_info = [InfoItem(i) for i in [
			"READ THIS FIRST",
			"hide these items by clicking the gray X next to each",
			"unhide all by clicking the dots",
			"this stuff will go to a menu but for now..",
			"ctrl + =,- : font size", 
			"f9 : only valid items in menu",
			"f8 : toggle the silly blue lines from Refs to their targets",
			"f5 : eval",
			"f4 : clear eval results",
			"f2 : replay previous session",
			"ctrl + up, down: menu movement",
			"space: menu selection",
			"",
			"red <>'s enclose nodes or other widgets",
			["green [text] are textboxes: ", ElementTag(nodes.Text("banana"))],
			["Compiler looks like this: ", ElementTag(nodes.Compiler(nodes.b['type']))],
			"(in gray) is the expected type",
			"currently you can only insert nodes manually by selecting them from the menu, with prolog, the compiler will start guessing what you mean:)"
		]]
		#,	"f12 : normalize syntaxes"
		s.hierarchy_infoitem = InfoItem("bla")
		s.deffun_infoitem = InfoItem("bla")
		s.hidden_toggle = widgets.Toggle(s, True, ("(.....)", "(...)"))
		s.hidden_toggle.color = s.hidden_toggle.brackets_color = "info item visibility toggle"

	@property
	def used_height(s):
		return len(s.lines) * font_height

	def update(s):
		s.items = []
		
		uc = s.root.under_cursor()
		s.items.append(s.hierarchy_infoitem)
		s.hierarchy_infoitem.contents = [
			str(s.root.cursor_c) + ":"+
			str(s.root.cursor_r)+ ":" + str(uc)]

		if isinstance(uc, nodes.FunctionCall):
			s.deffun_infoitem.contents = ["=>", ElementTag(uc.target)]
			s.items.append(s.deffun_infoitem)

		s.items += s.top_info[:]

	def tags(s):
		yield [ColorTag("help"), TextTag("help:  "), ElementTag(s.hidden_toggle), "\n"]
		for i in s.items:
			if not s.hidden_toggle.value or i.visibility_toggle.value:
				yield [ElementTag(i), "\n"]
		yield [EndTag()]

	def render(s):
		s.update()
		s.project()

	def _draw(s, surface):
		s.draw_lines(surface)


#todo: function definition / insight frame? preferably able to float in multiple numbers around the code
#status / action log window <- with keypresses too
#toolbar (toolbar.py)
#settings, the doc?
