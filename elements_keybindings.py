from keys import *
from tags import *

import nodes as n
import widgets as w

""" an event comes with two lists of attributes, one for the char(cell) that was on the left
of the cursor and one for the right. If either side doesnt belong to the element whose handler
we are examining, it is set to None
a handler is made to act on one or any of the sides(chars), # or perhaps not care - zero width elements
so the sidedness of the handler, has to match the sidedness of the event in regard to the element
"""
ANY = 0
LEFT = 1
RIGHT = 2
NONE = 3

H = collections.NamedTuple("Handler", 'side mods key')
#condition function?

"""
widgets.py
"""

def k_backspace (s, e):
	pos = e.left[body_pos_att]
	self.text = self.text[0:pos-2] + self.text[pos-1:]
	return s.after_edit(-1)
w.Text.k_backspace = k_backspace

def k_delete(s, e):
	pos = e.right[body_pos_att]
	s.text = s.text[0:(pos-1)] + s.text[pos:]
	return s.after_edit(0)
w.Text.k_delete = k_delete

def k_unicode(s, e):
	if e.key == K_ESCAPE:
		return False
	atts = e.left
	if not atts:
		atts = e.right
	if not atts: # we may want to have zero width elements later
		atts = e.between

	pos = atts[char_index_att]
	s.text = s.text[:(pos-1)] + e.uni + s.text[(pos-1):]
	return s.after_edit(e.uni)
w.Text.k_unicode = k_unicode


w.Text.keys = {H(LEFT,  [], K_BACKSPACE): w.Text.k_backspace,
			   H(RIGHT, [], K_DELETE): w.Text.k_delete,
			   H(NONE,  [], UNICODE): w.Text.k_unicode}


def press(self, e):
	self.on_press.emit(self)
	return s.CHANGED

w.Button.press = press

w.Button.keys = {H(NONE, [], (K_RETURN, K_SPACE)): w.Button.press}

w.NState.keys = {H(NONE, [], (K_RETURN, K_SPACE)): w.NState.toggle}

"""
nodes.py
"""


def eval(s):
	s.eval()
	return CHANGED

def delete_self(s):
	s.parent.delete_child(s)
	return AST_CHANGED

n.Node.keys = {
	H(NONE, [], K_F7): eval,
	H(NONE, [KMOD_CTRL], K_DELETE): delete_self}


n.Syntaxed.keys = n.Node.keys.update({
	H(NONE, [KMOD_CTRL], K_PERIOD): n.Syntaxed.prev_syntax,
    H(NONE, [KMOD_CTRL], K_COMMA ): n.Syntaxed.next_syntax})


def delete_item_check(s):
	return None != self.item_index(e)

def delete_item(s):
	ii = self.item_index(e)
	del self.items[ii]
	return CHANGED

def newline(s):
	item_index = self.item_index(e)
	self.newline(item_index)
	return CHANGED

n.List.keys = n.Collapsible.__bases__[-1].keys.update(
	{[  (NONE, [KMOD_CTRL], K_DELETE): (delete_item_check, delete_item),
		(NONE, [], K_RETURN): newline)]})





#i guess this goes in Editor...

def element_keypress(event):
	event.atts = namedtuple('atts', 'left right')(event.atts)

	r = handle_keypress(event)

	if r:
		elem, handler_result = r
		if handler_result:
			module = elem.module
			if module:
				event.final_root_state = deepcopy(editor.root) #for undo and redo. todo.


def handle_keypress(event):
	for side in [0,1]: #left, right
		atts = e.atts[side]
		if atts:
			elem = atts[node_att]
			h = find_handler(left_handlers, event)
			if h:
				return elem, fire(elem, h, event)


def find_handler(handlers, e):
	for h in handlers:
		if matches(h, e):
			return (h, e)


def fire(elem, handler, event):
	if h.side != BOTH:
		if h.side != LEFT:
			event = copy(event)
			event.left = None
		if h.side != RITE:
			event = copy(event)
			event.right = None
	return handler.func(elem, event)

