"""root, menu, log, info, help.."""
#todo:rename root to code or main or document or..
from __future__ import unicode_literals

import graph

import lemon_platform as platform
from lemon_colors import color, colors
import project
import nodes
from element import Element
from menu_items import InfoItem
from tags import TextTag, ElementTag, MemberTag, ColorTag, EndTag, AttTag
import widgets
from lemon_utils.lemon_logger import log, topic
from keys import *
from lemon_utils.lemon_six import iteritems, str_and_uni
from lemon_args import args
from lemon_utils.utils import evil
#todo:refactor stuff common to Menu and Info to some SimpleFrame or something


class Frame(object):
#	def on_mouse_press(self, e):
#	def on_keypress(self, e):
#	def draw(self):

	def __init__(s):
		s.lines = [] # lines actually on screen
		s.scroll_lines = 0 # how many lines the user has scrolled
		s._render_lines = {}#hack to satisfy project_elem(), not used here

	def on_keypress(self, event):
		return False

	def project(s):
		s.lines = project.project(s, # calls back our tags()
		    s.cols, s,
		    s.scroll_lines + s.rows  # bottom cut off
		).lines[s.scroll_lines:] # top cut off


	def under_cr(self, cr):
		c,r = cr
		try:
			return self.lines[r][c][1]["node"]
		except:
			return None

	def click_cr(s,e):
		node = s.under_cr(e.cr)
		if not node or not node.on_mouse_press(e.button):
			s.cursor_c, s.cursor_r = e.cr

	def mousedown(s,e):
		if e.button == 1:
			s.click(e)
		elif e.button == 4:
			s.scroll(-5)
		elif e.button == 5:
			s.scroll(5)

	def scroll(s,l):
		s.scroll_lines += l
		if s.scroll_lines < 0:
			s.scroll_lines = 0


class Root(Frame):
	def __init__(self):
		super(Root, self).__init__()
		self.cursor_c = self.cursor_r = 0
		self.root = nodes.make_root()
		self.root.fix_parents()
		self.arrows_visible = True
		self.cursor_blink_phase = True
		self.menu_dirty = True

		if args.noalpha:
			self.arrows_visible = False

	def and_sides(s,e):
		if e.all[K_LEFT]: s.move_cursor_h(-1)
		if e.all[K_RIGHT]: s.move_cursor_h(1)

	def and_updown(s,event):
		if event.all[K_UP]: s.move_cursor_v(-1)
		if event.all[K_DOWN]: s.move_cursor_v(1)

	@property
	def under_cursor(self):
		return self.under_cr((self.cursor_c, self.cursor_r))

	def first_nonblank(self):
		r = 0
		for ch, a in self.lines[self.cursor_r]:
			if ch == " ":
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

	def render(self):
		return collect_elem(self.root)
		self.lines = p.lines[self.scroll_lines:]
		self.arrows = self.complete_arrows(p.arrows)
		self.do_post_render_move_cursor()

		if False:#__debug__:  #todo: __debug__projection__ or something, this is eating quite some cpu i think and only checks the projection code (i think)
			assert(isinstance(self.lines, list))
			for l in self.lines:
				assert(isinstance(l, list))
				for i in l:
					assert(isinstance(i, tuple))
					assert(isinstance(i[0], str_and_uni))
					assert(len(i[0]) == 1)
					assert(isinstance(i[1], dict))
					assert(i[1]['node'])
					assert('char_index' in i[1])

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


	def prev_elem(s):
		e = s.under_cursor
		while s.move_cursor_h(-1):
			if e != s.under_cursor:
				break

	def run(s):
		s.root['some program'].run()

	def run_line(s):
		s.root['some program'].run_line(s.under_cursor)

	def clear(s):
		s.root['some program'].clear()

	def toggle_arrows(s):
		s.arrows_visible = not s.arrows_visible

	def	dump_to_file(s):
		f = open("dump.txt", "w")
		for l in s.lines:
			for ch in l:
				f.write(ch[0])
			f.write("\n")
		f.close()

	@topic('parents')
	def dump_parents(self):
		element = self.under_cursor
		while element != None:
			assert isinstance(element, Element), (assold, element)
			log(str(element))
			assold = element
			element = element.parent


	def do_post_render_move_cursor(s):
		if isinstance(s.server.root.post_render_move_caret, int):
			s.move_cursor_h(s.root.post_render_move_caret)
		else: #its a node
			log("moving cursor to " +str(s.root.post_render_move_caret))
			s.cursor_c, s.cursor_r = project.find(s.root.post_render_move_caret, s.lines)
		s.root.post_render_move_caret = 0


class Menu(Frame):
	def __init__(s, root):
		super(Menu, s).__init__()
		s.root = root
		s.sel = 0
		#index to items_on_screen. not ideal.
		#todo: a separate wishedfor_sel
		s.valid_only = False

	@property
	def selected(s):
		assert(s.sel != -1)
		if s.sel >= len(s.items_on_screen):
			return None
		#log("sel:", s.sel, s.items_on_screen)
		return s.items_on_screen[s.sel]

	def clamp_sel(s):
		if s.sel >= len(s.items_on_screen):
			s.sel = len(s.items_on_screen) - 1
		if s.sel < 0:
			s.sel = 0

	def render(s):
		s.project()
		s.clamp_sel()

	def tags(s):
		s.items_on_screen = []
		yield ColorTag("fg")
		for i in s.generate_palette():
			s.items_on_screen.append(i)
			yield [AttTag("node", i), ElementTag(i), EndTag(), "\n"]
		yield EndTag()

	def generate_palette(s):
		e = s.element = s.root.under_cursor
		atts = s.root.atts
		if e != None:
			for i in e.menu(atts):
				if not s.valid_only or i.valid:
					yield i


	def menu_dump(s):
		e = s.element = s.root.under_cursor
		atts = s.root.atts
		if e != None:
			e.menu(atts, True)


	def click(s,e):
		for i,r in iteritems(s.rects):
			if collidepoint(r, e.pos):
				s.sel = s.items_on_screen.index(i)
				s.accept()
				break

	def accept(self):
		if len(self.items_on_screen) > self.sel:
			if self.element.menu_item_selected(self.items_on_screen[self.sel], self.root.atts):
				self.sel = 0
				self.scroll_lines = 0
				return True


	def move(self, y):
		self.sel += y
		self.clamp_sel()

	def toggle_valid(s):
		s.valid_only = not s.valid_only


def collidepoint(r, pos):
	x, y = pos
	return x >= r[0] and y >= r[1] and x < r[0] + r[2] and y < r[1] + r[3]


class InfoFrame(Frame):
	info = []
	def __init__(s):
		super(InfoFrame, s).__init__()
		s.name = s.__class__.__name__

	def	must_re_collect(s):
		return False

	def tags(s):
		yield [ColorTag("help"), s.name + ":  "+"\n"]
		for i in s.items:
			yield i
			yield ["\n"]
		yield [EndTag()] # color


class GlobalKeys(InfoFrame):
	items = ["ctrl + =,- : font size",
			"f5 : eval",
			"f4 : clear eval results",
			"f2 : replay keypresses from previous session",
			"ctrl + up, down: menu movement",
			"space: menu selection",
	        "ctrl + d : dump root frame to dump.txt",
	        "ctrl + p : dump parents",
	        "ctrl + g : generate graph.gif",

			"f9 : only valid items in menu - doesnt do much atm",
			"f8 : toggle the silly arrows from Refs to their targets, (and current node highlighting, oops)"]

class NodeInfo(InfoFrame):
	def __init__(s, root):
		super(NodeInfo, s).__init__(root)
		#s.node_infoitem = InfoItem("bla")
		#s.deffun_infoitem = InfoItem("bla")

	def update(s):
		super(NodeInfo, s).update()
		uc = s.root.under_cursor
		while uc != None:
			if isinstance(uc, nodes.FunctionCall):
				s.items.append(InfoItem(["target=", ElementTag(uc.target)]))

			if uc.keys_help_items == None:
				uc.generate_keys_help_items()
			s.items += uc.keys_help_items

			uc = uc.parent

		uc = s.root.under_cursor
		while uc != None:
			s.items.append(InfoItem([
				str(s.root.cursor_c) + ":"+ str(s.root.cursor_r)+ ":" + 
				uc.long__repr__()]))
			uc = uc.parent


class Intro(InfoFrame):
	items = ["welcome to lemon!",
		    "press F1 to cycle this sidebar",
			"hide help items by clicking the gray X next to each",
			"unhide all by clicking the dots",
	        "scrolling with mousewheel is supported",
	        "",
			"nodes:",
			"red <>'s enclose nodes or other widgets",
			["green [text] are textboxes: ", ElementTag(nodes.Text("banana"))],
			#["{Parser} looks like this: ", ElementTag(nodes.Parser(nodes.b['type']))],
			#"(in gray) is the expected type",
		    "see intro.txt for hopefully more info"]



class Log(InfoFrame):
	def __init__(s):
		super(Log, s).__init__()
		s.items = []

	def add(s, msg):
		#timestamp, topics, text = msg
		#if type(text) != unicode:
		s.items.append(str(msg))
		print(str(msg))




#todo: function definition / insight frame? preferably able to float in multiple numbers around the code
#status / action log window <- with keypresses too
#toolbar (toolbar.py)
#settings, the doc?
