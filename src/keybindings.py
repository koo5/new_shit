from lemon_platform import SDL, CURSES
from lemon_utils.utils import odict
from lemon_utils.lemon_six import iteritems
from keys import *
from server_side import server as s
import replay


def change_font_size(x):
	"""dummy for the curses frontend, set from sdl_client"""
	pass


def die():
	if not replay.we_are_replaying: c.bye()





def keypress(e):
	h = find_handler(e)
	if h:
		pass_e = check = False
		if type(h) == tuple:
			if len(h) >= 3:
				check = h[2] == CHECK
				pass_e= h[2] == PASS_E
			h = h[0]
		if pass_e:
			h(e)
		elif not h() and check:
			s.editor.keypress(e)
	else:
		s.editor.keypress(e)


def find_handler(e):
	if e.mods in global_keys:
		h = global_keys[e.mods]
		return h.get(e.uni) or h.get(e.key)




HIDDEN = 0
CHECK = 1
PASS_E = 2
global_keys = {}
c = 666




def setup(client):
	global c
	c = client
	global_keys[frozenset()] = odict([
		(K_F1, c.cycle_sidebar),
		(K_F2, replay.do_replay),
		#K_F8: c.editor.toggle_arrows,
		(K_UP, (lambda e:(
		(c.editor.move_cursor_v(-1),
				c.editor.and_sides(e))), HIDDEN, PASS_E)),
		(K_DOWN,(lambda e:(
		(c.editor.move_cursor_v(+1),
			c.editor.and_sides(e))), HIDDEN, PASS_E)),
		(K_LEFT,(lambda e:(
		(c.editor.move_cursor_h(-1),
			c.editor.and_updown(e))), HIDDEN, PASS_E)),
		(K_RIGHT,(lambda e:(
		(c.editor.move_cursor_h(+1),
			c.editor.and_updown(e))), HIDDEN, PASS_E)),
		(K_HOME,
			(c.editor.cursor_home, HIDDEN)),
		(K_END,
			(c.editor.cursor_end, HIDDEN)),
		(K_PAGEUP,
			(lambda:c.editor.move_cursor_v(-10), HIDDEN)),
		(K_PAGEDOWN,
			(lambda:c.editor.move_cursor_v(10), HIDDEN)),
		(K_ESCAPE,
			die),
		(K_SPACE,
			(s.menu.accept, None, CHECK))
	])

	global_keys[frozenset([KMOD_CTRL])] = odict([
		('=',
			(lambda:change_font_size(1),'inc font size')),
		('-',
			(lambda:change_font_size(-1),'dec font size')),
		(K_LEFT,
			c.editor.prev_elem),
		(K_RIGHT,
			c.editor.next_elem),
		(K_HOME,
			c.editor.cursor_top),
		(K_END,
			c.editor.cursor_bottom),
		(K_f,
			c.editor.dump_to_file),
		(K_x,
			c.editor.counterpart.cut),
		(K_c,
			c.editor.counterpart.copy),
		(K_b,
			c.editor.counterpart.paste),
		(K_m,
			s.menu.menu_dump)


	])

	#global_keys[frozenset([KMOD_RSHIFT])] = odict([
	#	(K_INSERT,
	#	 (lambda: c.cycle_sidebar, 'paste'))])

	if SDL:
		global_keys[frozenset([KMOD_CTRL])].update(odict([
			(K_UP,
			 (lambda:c.sidebar.move(-1), "menu up")),
			(K_DOWN,
			 (lambda:c.sidebar.move(1), "menu down"))]))

	s.node_info.global_keys = (["global keys:"]+
		list(handler_str([])) +
		["ctrl "+x for x in handler_str([KMOD_CTRL])])

def handler_str(mod):
	for k,h in iteritems(global_keys[frozenset(mod)]):
		name = None
		if type(h) == tuple:
			if h[1] == HIDDEN:
				continue
			elif type(h[1]) == str:
				name = h[1]
			h = h[0]
		if name == None:
			name = h.__name__
		yield key_str(k) + ": " + name


def key_str(k):
	return s.key_to_name(k) if not type(k) == str else '"'+k+'"'


"""here we count on the fact that each client frame has been assigned to an
attribute of the server module. to do this with rpcing,
clients or client frames will have to act as servers too, with the messaging
loop integrated with the gui loop"""

#maybe when we have multiple editor frames,
#we will want to just pass the event on to perhaps the previously focused frame
#for now im trying having all top level handlers in one file here

#todo:look into FRP

#curses enter: http://lists.gnu.org/archive/html/bug-ncurses/2011-01/msg00011.html


