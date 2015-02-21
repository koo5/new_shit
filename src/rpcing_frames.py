from math import atan2, cos, sin
from pprint import pformat as pp

from lemon_platform import SDL, CURSES
from lemon_utils.lemon_logging import log
from lemon_utils.lemon_six import iteritems, unicode
from lemon_args import args
from lemon_utils.utils import Evil
from lemon_utils.cache import Cache
from lemon_colors import colors

import graph
import nodes
from element import Element
from menu_items import InfoItem
from tags import *
import widgets
from keys import *
from server_side import server

if SDL:
	import pygame
	from pygame import Rect

class Line():
	__slots__ = ['font', 'chars']
	def __init__(s, font, chars):
		s.font = font
		s.chars = chars
		assert type(font) == Font

class Font():
	__slots__ = ['font', 'width', 'height']
	def __init__(s, font, width, height):
		s.font = font
		s.width = width
		s.height = height

class ClientFrame(object):

	def __init__(s, counterpart):
		super().__init__()
		s.visible = True
		s.arrows = []
		s.must_redraw = True
		s._scroll_lines = 0
		s.indent_width = 4
		s.counterpart = counterpart
		s.tags = Cache(s.counterpart.collect_tags)
		s.lines = Cache(s.project)
		s.counterpart.draw_signal.connect(s.maybe_redraw)

	@property
	def scroll_lines(s):
		return s._scroll_lines
	@scroll_lines.setter
	def scroll_lines(s, x):
		if s._scroll_lines != x:
			s._scroll_lines = x
			s.tags.dirty = s.lines.dirty = True
			log("scroll_lines:%s", x)

	@property
	def rect(s):
		return s._rect
	@rect.setter
	def rect(s, x):
		s._rect = x
		#s.lines.dirty = True
		s.tags.dirty = s.lines.dirty = True

	#frames with default font have it easy
	@property
	def cols(s):
		return s.rect.width // get_font(0).width
	@property
	def rows(s):
		return s.rect.width // get_font(0).height


	def project(s):
		s.completed_arrows = None
		return s.project_tags(s.tags.get())

	def maybe_redraw(s):
		"""non-rpcing client overrides this with a
		function that maybe_draws all frames in the window at once"""
		Xself.maybe_draw()

	def maybe_draw(s):
		if not s.visible: return
		must_recollect = s.counterpart.must_recollect()
		if must_recollect:
			s.tags.dirty = s.lines.dirty = True
		if must_recollect or s.lines.dirty or s.tags.dirty or s.must_redraw:# or not args.rpc:
			log("drawing %s, must_recollect = %s, lines.dirty = %s, must_redraw = %s", s.counterpart, must_recollect, s.lines.dirty, s.must_redraw)
			s.draw()
			s.must_redraw = False

	if CURSES:
		def draw(s):
			s.curses_win.clear()
			s.curses_draw_stuff()
	elif SDL:
		def draw(s):
			if s.rect.h == 0 or s.rect.w == 0:
				return
			surface = pygame.Surface((s.rect.w, s.rect.h), 0)
			if colors.bg != (0,0,0):
				surface.fill(colors.bg)
			s.sdl_draw_stuff(surface)
			sdl_screen_surface.blit(surface, s.rect.topleft)

	def sdl_draw_lines(s, surf, highlight=None, transparent=False, just_bg=False):
		y = 0

		for row, line in enumerate(s.lines.get()):
			assert type(line) == Line
			if row < s.scroll_lines:
				continue

			font = line.font
			assert type(font) == Font

			fisheye = args.fisheye and type(s) == Editor and row == s.cursor_r
			if fisheye:
				y += args.line_spacing
				font = get_font(1)

			y += font.height

			s.sdl_draw_line(surf, line.chars, line.font, y, highlight, transparent, just_bg)

			if row == s.rows + s.scroll_lines:
				break

			y += args.line_spacing

			if fisheye:
				y += args.line_spacing

	@staticmethod
	def sdl_draw_line(surf, chars, font, y, highlighted_element=None, transparent=False, just_bg=False):
		for col, char in enumerate(chars):
			x = font.width * col

			hi = highlighted_element and char[1].get(Att.elem) == highlighted_element

			if hi:
				bg = colors.highlighted_bg
				if just_bg:
					pygame.draw.rect(surf,bg,(x,y,font.width,font.height))
			else:
				bg = colors.bg

			if not just_bg:
				fg = char[1][Att.color]
				if transparent:
					bg = None
				rect = font.font.get_rect(char[0])
				font.font.render_to(surf, (x+rect.x,y-rect.y), None, fg, bg)# - ?!



	if CURSES:
		def curses_draw_lines(s, win):
			for row, line in enumerate(s.lines):

				#lets implement scrolling here, for once. Im still pondering a proper, somewhat element-based solution
				real_row = row + s.scroll_lines
				if real_row < 0:
					continue
				if real_row > s.rows:
					return

				assert len(line) <= s.cols
				s.draw_line(win, line)

		def curses_draw_line(s, win, line):
			for col, char in enumerate(line):
				mode = 0
				try:
					if char[1][Att.elem] == s.highlight:
						mode = c.A_BOLD + c.A_REVERSE
				except:	pass
				try:
					win.addch(row,col,ord(char[0]), mode)
				except c.error:#it throws an error to indicate last cell
					if (row+1, col+1) != win.getmaxyx():
						raise


	def project_tags(s,batches):
		"""
		#these are the tags that come over the wire:
		# unicode,
		# attribute tuple, end_tag,
		# indent_tag, dedent_tag,
		# dict with custom stuff
		"""
		s.zwes = {}
		chars = []
		atts = []
		char_index = 0
		indentation = 0
		lines_count = 0
		editable = False
		font = Evil('font')
		line_cols = Evil("line cols")

		def switch_font(level = 0):
			nonlocal font, line_cols
			font = get_font(level)
			line_cols = (s.rect.width-1) // font.width

		def indent():
			numspaces = indentation * s.indent_width
			spaceleft = line_cols - len(chars)
			for i in range(min(numspaces, spaceleft)):
				append(' ')

		def append(char):
			chars.append((char, atts_dict()))

		def current_cr():
			return (len(chars), lines_count)

		def add_zwe():
			s.zwes[current_cr()] = atts_dict()

		def atts_dict():
			#calling a dict() with atts, which is a list of tuples (key, value)
			#"squashes" it, the more recently appended attributes overwrite the older ones
			return dict(atts + [(Att.char_index, char_index)])

		switch_font()

		for batch in batches:

			for tag in batch:

				if type(tag) == tuple: # an attribute tuple
					atts.append(tag)

				elif tag == end_tag:
					atts.pop()

				elif type(tag) == unicode:
					for char in tag:
						if editable:
							add_zwe()
						if char != "\n":
							append(char)
							char_index += 1
						if len(chars) == line_cols or char == "\n":
							yield Line(font, chars)
							chars = []
							if char == "\n":
								switch_font()#back to default
							indent()
							lines_count += 1


				elif tag == indent_tag:
					indentation += 1

				elif tag == dedent_tag:
					indentation -= 1
					assert indentation >= 0

				elif tag == editable_start_tag:
					editable = True
					char_index = 0
				elif tag == editable_end_tag:
					editable = False
					add_zwe()
				elif tag == zwe_tag:
					add_zwe()

				elif type(tag) == dict:
					if 'arrow' in tag:
						s.arrows.append(current_cr() + (tag['arrow'],))
					elif 'font_level' in tag:
						switch_font(tag['font_level'])
					#elif 'long_text' in tag:

					else:
						wat

				else:
					raise Exception("is %s a tag?, %s" % (repr(tag)))

		yield Line(font, chars)


		"""
		def test():
			project_tags([[
				(Att.color, (0,0,0)),
				"hey",
				"how does this work\n\n",
				(Att.elem, 333),
				"wut wut",
				pop_tag,
			    indent_tag,
			    "yo!\n",
			    dedent_tag
	              ]])
		"""


	@property
	def cursor(s):
		return s.cursor_c, s.cursor_r

	def under_cr(s, cr):
		atts = s.atts_at_cr(cr)
		if atts:
			return atts[Att.elem]

	@property
	def under_cursor(s):
		return s.under_cr(s.cursor)

	@property
	def atts_at_cursor(s):
		return s.atts_at_cr(s.cursor)

	def atts_at_cr(s, cr):
		c,r = cr
		try:
			return s.lines[r+s.scroll_lines].chars[c][1]
		except IndexError:
			return None

	def click_cr(s,e):
		elem = s.under_cr(e.cr)
		if not elem or not s.counterpart.on_elem_mouse_press(elem, e.button):
			s.click_fallthrough(e.cr)

	def click_fallthrough(s, cr):
		pass

	def scroll(s,l):
		sl = s.scroll_lines + l
		if sl < 0:
			sl = 0
		s.scroll_lines = sl
		s.must_redraw = True
		s.maybe_redraw()


	def sdl_mousedown(s,e):
		if e.button == 4:
			s.scroll(-1)
		elif e.button == 5:
			s.scroll(1)
		else:
			e.cr = s.sdl_xy2cr(e.pos) #mouse xy to column, row
			s.click_cr(e)



	def sdl_cursor_xy(s,c,r):
		x = c * s.lines[r].font.width
		y = 0
		for row, line in enumerate(s.lines):
			fh = line.font.height
			if row == r:
				return (x, y, y + fh)
			else:
				y += fh + args.line_spacing

	def sdl_xy2cr(s, xy):
		x,y = xy
		for row, line in enumerate(s.lines):
			if row < s.scroll_lines: continue
			y -= line.font.height + args.line_spacing
			if y < 0:
				return (x//line.font.width, row-s.scroll_lines)




class Editor(ClientFrame):
	def __init__(s):
		super().__init__(server.editor)
		s.cursor_c = s.cursor_r = 0
		s.zwes = 666
		if SDL:
			s._cursor_blink_phase = True
			s.arrows_visible = not args.noalpha and args.arrows

	if SDL:
		@property
		def cursor_blink_phase(s):
			return s._cursor_blink_phase
		# O B E Y T H E B O I L E R P L A T E
		@cursor_blink_phase.setter
		def cursor_blink_phase(s, v):
			if s._cursor_blink_phase != v:
				s._cursor_blink_phase = v
				s.must_redraw = True

	def and_sides(s,e):
		if e.all[K_LEFT]:
			log('moving diagonally:-)')
			s.move_cursor_h(-1)
		if e.all[K_RIGHT]:
			log('moving diagonally:-)')
			s.move_cursor_h(1)

	def and_updown(s,event):
		if event.all[K_UP]:
			log('moving diagonally:-)')
			s.move_cursor_v(-1)
		if event.all[K_DOWN]:
			log('moving diagonally:-)')
			s.move_cursor_v(1)

	def first_nonblank(s):
		r = 0
		for ch, a in s.lines[s.cursor_r+s.scroll_lines].chars:
			if ch == " ":
				r += 1
			else:
				return r

	def _move_cursor_h(s, x):
		"""returns True if it moved"""
		old = s.cursor_c, s.cursor_r, s.scroll_lines
		s.cursor_c += x
		if len(s.lines) <= s.cursor_r+s.scroll_lines or \
						s.cursor_c > len(s.lines[s.cursor_r+s.scroll_lines].chars):
			s._move_cursor_v(x)
			s.cursor_c = 0
		if s.cursor_c < 0:
			if s._move_cursor_v(-1):
				s.cursor_c = len(s.lines[s.cursor_r+s.scroll_lines].chars)
			else:
				s.cursor_c = 0
		moved = old != (s.cursor_c, s.cursor_r, s.scroll_lines)
		return moved

	def move_cursor_h(s, count):
		if s._move_cursor_h(count):
			s.after_cursor_moved()

	def _move_cursor_v(s, count):
		"""returns True if it moved"""
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
		moved = old != (s.cursor_c, s.cursor_r, s.scroll_lines)
		return moved

	def move_cursor_v(s, count):
		log("move_cursor_v %s",count)
		if s._move_cursor_v(count):
			s.after_cursor_moved()

	def prev_elem(s):
		e = s.under_cursor
		while s._move_cursor_h(-1):
			if e != s.under_cursor:
				s.after_cursor_moved()
				break

	def next_elem(s):
		e = s.under_cursor
		while s._move_cursor_h(1):
			if e != s.under_cursor:
				s.after_cursor_moved()
				break

	def cursor_home(s):
		if len(s.lines) > s.cursor_r+s.scroll_lines: # dont try to home beyond the end of file
			if s.cursor_c != 0:
				s.cursor_c = 0
			else:
				s.cursor_c = s.first_nonblank()
			s.after_cursor_moved()

	def cursor_end(s):
		if len(s.lines) > s.cursor_r+s.scroll_lines:
			s.cursor_c = len(s.lines[s.cursor_r+s.scroll_lines].chars)
			s.after_cursor_moved()

	def cursor_top(s):
		s.cursor_r = 0
		s.after_cursor_moved()

	def cursor_bottom(s):
		log("i was too lazy to implement this")
		s.after_cursor_moved()

	def after_project(s):
		s.do_post_render_move_cursor()
		s.complete_arrows()
		"""outdated
		if False:#__debug__:
			for l in s.lines:
				assert(isinstance(l, list))
				for i in l:
					assert(isinstance(i, tuple))
					assert(isinstance(i[0], unicode))
					assert(len(i[0]) == 1)
					assert(isinstance(i[1], dict))
					assert(Att.elem in i[1])
					assert(Att.char_index in i[1])
		"""
	def find_element(s, e):
		"""return coordinates of element in s.lines"""
		#assert(isinstance(e, int)),  e
		for l, line in enumerate(s.lines):
			for c,char in enumerate(line.chars):
				if char[1][Att.elem] == e:
					return c, l

	def do_post_render_move_cursor(s):
		m = s.counterpart.root.delayed_cursor_move

		if m.node:
			log("moving cursor to %s", m.node)
			pos = s.find_element(m.node)
			if pos:
				s._move_cursor_v(s.cursor_r - pos[1] + s.scroll_lines)
				s.cursor_c = pos[0]

		if m.chars:
			log("moving cursor by %s chars", m.chars)
			s._move_cursor_h(m.chars)

		if m.node != None or m.chars != 0:
			m.node = None
			m.chars = 0
			s.update_atts_on_server()

	def update_atts_on_server(s):
		s.counterpart.set_atts(s.atts_triple)

	def after_cursor_moved(s):
		log("after_cursor_moved: %s %s",s.cursor_c, s.cursor_r)
		s.must_redraw = True
		s.update_atts_on_server()
		s.maybe_redraw()

	def click_fallthrough(s, cr):
		s.cursor_c, s.cursor_r = cr
		s.after_cursor_moved()

	@property
	def atts_triple(s):
		#lets try moving the cursor to see if theres a char to the cursors left
		if s._move_cursor_h(-1):
			left = s.atts_at_cursor
			s._move_cursor_h(1) # undo the test move
		else:
			left = None

		right = s.atts_at_cursor
		middle = s.zwes.get((s.cursor_c, s.cursor_r+s.scroll_lines))

		return dict(left=left, middle=middle, right=right)

	def sdl_draw_stuff(s, surf):
		highlight = s.under_cursor if not args.eightbit else None

		if s.arrows_visible:
			s.sdl_draw_lines(surf, highlight,
			                 transparent=True)
			s.sdl_draw_arrows(surf)
		else:
			s.sdl_draw_lines(surf, highlight, False)
		s.after_project()
		s.draw_cursor(surf)


	""" def sdl_draw_stuff(s, surf):
		if s.arrows_visible:
			s.sdl_draw_lines(surf, highlight=s.under_cursor,
			                 transparent=Evil('justbg, so no transparent'),
			                 just_bg=True)
			s.sdl_draw_arrows(surf)
			s.sdl_draw_lines(surf, s.under_cursor, True)
		else:
			s.sdl_draw_lines(surf, s.under_cursor, False)
		s.draw_cursor(surf)"""


	def curses_draw_stuff(s, win):
		s.curses_draw_lines(win)

	def complete_arrows(s):
		s.completed_arrows = []
		if s.arrows_visible:
			for a in s.arrows:
				target = s.find_element(a[2])
				if target:
					s.completed_arrows.append(((a[0],a[1] - s.scroll_lines), target))

	def sdl_draw_arrows(s, surface):
		#todo: would be nice if the target ends of arrows faded out proportionally to the number of arrows on screen pointing to that same target, to avoid making it unreadable
		if s.completed_arrows == None:
			s.complete_arrows()
		for ((c,r),(c2,r2)) in s.completed_arrows:
			x,y,x2,y2 = font_width * (c+0.5), font_height * (r+0.5), font_width * (c2+0.5), font_height * (r2+0.5)
			pygame.draw.line(surface, colors.arrow, (int(x),int(y)),(int(x2),int(y2)))
			a = atan2(y-y2, x-x2)
			angle = 0.1
			length = 40
			sdl_arrow_side(length, a+angle, x2,y2, surface)
			sdl_arrow_side(length, a-angle, x2,y2, surface)


	def draw_cursor(s, surf):
		if s.cursor_blink_phase:
			x, y, y2 = s.sdl_cursor_xy(s.cursor_c, s.cursor_r)
			pygame.draw.rect(surf, colors.cursor, (x, y, args.font_size//8, y2 - y,))

	def toggle_arrows(s):
		s.arrows_visible = not s.arrows_visible
		s.must_redraw = True
		s.maybe_redraw()

	def	dump_to_file(s):
		f = open("dump.txt", "w")
		for l in s.lines:
			for ch in l.chars:
				f.write(ch[0])
			f.write("\n")
		f.close()






class SidebarFrame(ClientFrame):
	def move(s, x):
		s.counterpart.move(x)

	def get_items(s):
		for i in s.counterpart.get_items():
			yield SidebarItem(list(s.project_tags([i])))

	def sdl_draw_items(s, surface):
		done = False
		item_top_y = 0
		current_line = 0
		s.drawn_rects = {}

		for i, item in enumerate(s.get_items()):
			item_height = biggest_width = 0
			lines_to_draw = []
			for l in item.lines:
				if current_line >= s.scroll_lines:
					biggest_width = max(biggest_width, len(l.chars)*l.font.width)
					item_height += l.font.height
					lines_to_draw.append((l.chars, l.font, item_top_y + item_height))
					if item_top_y + item_height > s.rect.height:
						done = True
						break
				current_line += 1

			if item_height > 0:
				rect = Rect(0, item_top_y,
				            biggest_width,
				            item_height)
				s.drawn_rects[i] = rect

				is_selected = s.counterpart.sel == i
				color = colors.menu_rect_selected if is_selected else colors.menu_rect
				pygame.draw.rect(surface, color, rect, 1)

				item_top_y += item_height

			for i in lines_to_draw:
				s.sdl_draw_line(surface, *i)

			if done:
				return

	def sdl_draw_stuff(s, surface):
		s.sdl_draw_items(surface)


class InfoFrame(SidebarFrame):
	def __init__(s, counterpart):
		super().__init__(counterpart)



class Menu(SidebarFrame):
	def __init__(s, editor):
		super().__init__(server.menu)
		s.editor = editor

	def click(s,e):
		for i,r in iteritems(s.drawn_rects):
			if collidepoint(r, e.pos):
				s.counterpart.sel = i
				s.counterpart.accept()
				break


class Log(ClientFrame):
	def __init__(s):
		super().__init__(server.logframe)
		s.counterpart.on_add.connect(s.add)
		s.tags = Cache(s.collect_tags)
		s.items = []

	def collect_tags(s):
		for i in s.items:
			yield [i, '\n']

	def add(s, msg):
		#time, topic, text = msg
		print (msg)
		s.items.append(str(msg))

	def sdl_draw_stuff(s, surface):
		s.sdl_draw_lines(surface)






def draw(s, surface):
	s.draw_lines(surface)


class SidebarItem():
	def __init__(s, lines, rect=None):
		s.lines = lines
		s.rect = rect

def sdl_arrow_side(length,a,x2,y2, surface):
	x1y1 = int(length * cos(a) + x2), int(length * sin(a) + y2)
	pygame.draw.line(surface, colors.arrow, x1y1,(int(x2),int(y2)))


def collidepoint(r, pos):
	x, y = pos
	return x >= r[0] and y >= r[1] and x < r[0] + r[2] and y < r[1] + r[3]
