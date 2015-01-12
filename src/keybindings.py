from lemon_platform import SDL, CURSES
from keys import *
from server_side import server as s
import replay


def change_font_size(x):
	"""dummy"""
	pass

def keypress(e):
	if not global_key(e):
		s.editor.keypress(e)

#we should declarativize this too, just like element_keybindings

def global_key(e):
	k = e.key
	if KMOD_CTRL & e.mod:

		if e.uni == '=':
			change_font_size(1)
		elif e.uni == '-':
			change_font_size(-1)

		elif k == K_LEFT:
			c.editor.prev_elem()
		elif k == K_RIGHT:
			c.editor.next_elem()
		elif k == K_HOME:
			c.editor.cursor_top()
		elif k == K_END:
			c.editor.cursor_bottom()

		elif k == K_f:
			c.editor.dump_to_file()
		elif k == K_q:
			s.bye()
		elif e.key == K_m:
			s.menu.menu_dump()


		elif SDL and e.key == K_UP:
			c.sidebar.move(-1)
		elif SDL and e.key == K_DOWN:
			c.sidebar.move(1)

		elif CURSES and e.key == K_INSERT: # todo: find better keybindings for curses
			c.sidebar.move(-1)
		elif CURSES and e.key == K_DELETE:
			c.sidebar.move(1)
		else:
			return False
		return True


	else: # with no modifier keys
		if k == K_F1:
			c.cycle_sidebar()
		elif k == K_F2:
			replay.do_replay()
		elif k == K_F8:
			c.editor.toggle_arrows()

		elif k == K_UP:
			c.editor.move_cursor_v(-1)
			c.editor.and_sides(e)
		elif k == K_DOWN:
			c.editor.move_cursor_v(+1)
			c.editor.and_sides(e)
		elif k == K_LEFT:
			c.editor.move_cursor_h(-1)
			c.editor.and_updown(e)
		elif k == K_RIGHT:
			c.editor.move_cursor_h(+1)
			c.editor.and_updown(e)
		elif k == K_HOME:
			c.editor.cursor_home()
		elif k == K_END:
			c.editor.cursor_end()
		elif k == K_PAGEUP:
			c.editor.move_cursor_v(-10)
		elif k == K_PAGEDOWN:
			c.editor.move_cursor_v(10)

		elif k == K_ESCAPE:
			if not replay.we_are_replaying:
				c.bye()
		elif e.uni == ' ':
			return s.menu.accept()
		else:
			return False
		return True


"""here we count on the fact that each client frame has been assigned to an
attribute of the server module. to do this with rpcing,
clients or client frames will have to act as servers too, with the messaging
loop integrated with the gui loop"""

#maybe when we have multiple editor frames,
#we will want to just pass the event on to perhaps the previously focused frame
#for now im trying having all top level handlers in one file here

#todo:look into FRP

#curses enter: http://lists.gnu.org/archive/html/bug-ncurses/2011-01/msg00011.html


