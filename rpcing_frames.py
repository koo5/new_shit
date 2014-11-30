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
from lemon_logger import log, topic
from keys import *
from lemon_six import iteritems, str_and_uni
from lemon_args import args
from utils import evil
#todo:refactor stuff common to Menu and Info to some SimpleFrame or something

server = x


class ClientFrame(object):

	def scroll(s,l):
		s.scroll_lines -= l
		if s.scroll_lines < 0:
			s.scroll_lines = 0


	# lets try setting a reasonable rpc timeout on the proxy
	#and wrapping everything in a try except catching the timeout?

	#also, i will be adressing the server objects explicitly
	#or not...
	#instead of instantiating the client frames with references to the server counterparts
	#this way it will be easier to have it survive a reconnect/server restart..

	#		counterpart = core.log

	def maybe_draw(s):
		if s.counterpart.s.counterpart.must_re_collect():
			# todo set it on resize too
			s.must_re_collect = s.must_re_project = True
			s.draw()
			s.must_re_collect = s.must_re_project = False

	def do_draw(s):
		s.must_re_collect = s.must_re_project = True
		s.draw()
		s.must_re_collect = s.must_re_project = False


	@property
	def projected_lines(s):
		s._maybe_cached(s.must_reproject,
						s.project(s.collected_tags),
						s._projected_lines)

	@property
	def collected_tags(s):
		return s._maybe_cached(s.must_re_collect,
		                       server.collect_tags(s.counterpart) ,
		                       s._collected_tags)


	def _maybe_cached(get_fresh, generator, cache):
		if get_fresh:
			cache.clear()
			for item in generator:
				cache.append(item)
				yield item
		else:
			return cache

	def curses_draw_chars(self):
		win = s.curses_win
		s.curses_win.clear()

		for row, line in enumerate(self.projected_lines):

			#lets implement scrolling here, for once. Im still pondering a proper, somewhat element-based solution
			real_row = row + s.scroll_lines
			if real_row < 0:
				continue
			if real_row > s.rows:
				return

			assert len(line) <= self.cols
			for col, char in enumerate(line):
				mode = 0
				try:
					if char[1][att_node] == s.highlight:
						mode = c.A_BOLD + c.A_REVERSE
				except:	pass
				try:
					win.addch(row,col,ord(char[0]), mode)
				except c.error:
					#it throws an error to indicate last cell. what error?
					if (row+1, col+1) != win.getmaxyx():
						log(row,col,'of',  win.getmaxyx(),":",ord(char[0]))
						raise



#these are the tags that come over the wire:
# unicode,
# attribute tuple, end_tag,
# indent_tag, dedent_tag,
# dict with custom stuff



	def project_tags(batches):
		line = []
		atts = []
		char_index = 0
		indent = 0

		def newline():
			numspaces = indent * indent_width
			spaceleft = cols - len(line)
			to_go = min(spaceleft, numspaces)
			for i in xrange(0, to_go):
				line.append((' ', dict(atts))
				#calling a dict() with atts, which is a list of tuples (key, value)
				#"squashes" it, the last attributes (on top) overwrite the ones below


		for batch in batches:
			for tag in batch:

				if type(tag) == unicode:

					for char in tag:
						atts.append()
						if char == "\n":
							yield line
						else:
							line.append((char, atts + (att_char_index, char_index)))
							if len(line) == cols:
								yield line
							char_index += 1

				elif tag == end_tag:
					atts.pop()

				elif type(tag) == tuple: # an attribute tuple
					atts.append(tag)

				elif tag == indent_tag:
					indent += 1

				elif tag == dedent_tag:
					indent -= 1

				elif type(tag) == dict:
					s.arrows_append((len(line), len(s._projected_lines), tag.target))

				else:
					raise Exception("is %s a tag?, %s" % (repr(tag)))


		def test():
			#we would have to set cols somehow
			project_tags([[
				(color_att, (0,0,0)),
				"hey",
				"how does this work\n\n",
				(node_att, 333),
				"wut wut",
				pop_tag,
			    indent_tag,
			    "yo!\n",
			    dedent_tag
	              ]])




	def under_cr(self, cr):
		c,r = cr
		try:
			return self.lines[r][c][1][node_tag]
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





class Root(ClientFrame):
	def __init__(self):
		super(Root, self).__init__()
		self.cursor_c = self.cursor_r = 0
		self.cursor_blinking_phase = True

		self.arrows_visible = True and (
			not args.noalpha
			and lemon_platform.frontend == lemon_platform.sdl)

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
		for ch, a in self._projected_lines[self.cursor_r]:
			if ch == " ":
				r += 1
			else:
				return r


	def move_cursor_h(s, x):
		"""returns True if it moved"""
		old = s.cursor_c, s.cursor_r, s.scroll_lines
		s.cursor_c += x
		if len(s._projected_lines) <= s.cursor_r or \
						s.cursor_c > len(s._projected_lines[s.cursor_r]):
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



	def prev_elem(s):
		e = s.under_cursor
		while s.move_cursor_h(-1):
			if e != s.under_cursor:
				break

	def next_elem(s):
		e = s.under_cursor
		while s.move_cursor_h(1):
			if e != s.under_cursor:
				break

	def cursor_home(s):
		if len(s.lines) > s.cursor_r:
			if s.cursor_c != 0:
				s.cursor_c = 0
			else:
				s.cursor_c = s.first_nonblank()

	def cursor_end(s):
		if len(s.lines) > s.cursor_r:
			s.cursor_c = len(s.lines[s.cursor_r])

	def cursor_top(s):
		s.cursor_r = 0

	def cursor_bottom(s):
		log("hmpf")


	def draw(s):
		s.draw_lines()
		s.arrows = s.complete_arrows(s.arrows)
		s.do_post_render_move_cursor()

		if __debug__:  #todo: __debug__projection__ or something, this is eating quite some cpu i think and only checks the projection code (i think)
			for l in self._projected_lines:
				assert(isinstance(l, list))
				for i in l:
					assert(isinstance(i, tuple))
					assert(isinstance(i[0], unicode))
					assert(len(i[0]) == 1)
					assert(isinstance(i[1], dict))
					assert(node_att in i[1])
					assert(char_index_att in i[1])

	def complete_arrows(s):
		if not s.arrows_visible:
			s.arrows = []
		else:
			r = []
			for a in s.arrows:
				target = project.find(a[2], self._projected_lines)
				if target:
					r.append(((a[0],a[1] - self.scroll_lines),target))
			s.arrows = r


	def toggle_arrows(s):
		s.arrows_visible = not s.arrows_visible

	def	dump_to_file(s):
		f = open("dump.txt", "w")
		for l in s.lines:
			for ch in l:
				f.write(ch[0])
			f.write("\n")
		f.close()


	def do_post_render_move_cursor(s):
		where = s.counterpart.root.post_render_move_caret
		if isinstance(where, int): # by this many chars
			s.move_cursor_h(where)
		else: #to a node, lets indicate it with a tuple hmmm
			where = where[0]
			log("moving cursor to node " +str(where))
			s.cursor_c, s.cursor_r = s.find(where)
		s.counterpart.root.post_render_move_caret = 0


	@property
	def atts_at_cursor(self):
		try:
			return self.lines[self.cursor_r][self.cursor_c][1]
		except IndexError:
			return None


	@property
	def atts(self):
		#for now, if the cursor isnt strictly on a char that was rendered, we return None

		#lets try moving the cursor to see if theres a char to the cursors left
		if move_cursor_h(-1):
			left = atts_at_cursor()
			move_cursor_h(1) # and move it back
		else:
			left = None

		right = atts_at_cursor()

		return left, right

	def keypress_on_element(event):
		#event.cursor = (s.cursor_c, s.cursor_r)
		event.atts = self.atts

		server.on_keypress(event)



class InfoFrame(ClientFrame):
	def __init__(s, counterpart):
		super(InfoFrame, s).__init__()
		s.counterpart = counterpart









class Menu(Frame):
	def __init__(s, root):
		super(Menu, s).__init__()

	def on_keypress(self, e):
		if platform.frontend == platform.sdl and e.mod & KMOD_CTRL:
			if e.key == K_UP:
				self.move(-1)
				return True
			elif e.key == K_DOWN:
				self.move(1)
				return True
			elif e.key == K_m:
				self.menu_dump()
				return True
		elif platform.frontend == platform.curses:
			if e.key == K_INSERT:
				self.move(-1)
				return True
			elif e.key == K_DELETE:
				self.move(1)
				return True
			
		#if e.key == K_SPACE:
		if e.uni == ' ':
			return self.accept()

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


class Log(InfoFrame):
	def __init__(s):
		super(Log, s).__init__(evil('no root needed'))
		s.items = []
		s.projected = []
		s.top_bar = [ColorTag("help"), TextTag(s.name + ":  "), ElementTag(s.hidden_toggle)]
		s.cols = 20#maybe we should just postpone the rendering until update()..setting cols here so add() doesnt crap out

	def render(s):
		s.lines = project.project_tags(s.top_bar, s.cols, s).lines
		s.lines += s.projected[-s.rows-s.scroll_lines:][:s.rows-len(s.lines)]
		#print len(s.projected)
		#print s.rows, s.scroll_lines, len(s.lines), len([x for x in s.tags()])

	def update(s):
		pass

	def add(s, text):
		text = time.strftime("%H:%M:%S:%f", time.localtime()) + text
		it = InfoItem(text)
		s.items.append(it)
		s.projected += project.project_tags([ColorTag("fg"), ElementTag(it)], s.cols, s).lines


