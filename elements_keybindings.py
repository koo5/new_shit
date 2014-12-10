import collections

from keys import *
from tags import *

import nodes as n
import widgets as w

from lemon_utils.utils import odict

""" an event comes with two lists of attributes, one for the char(cell) that was on the left
of the cursor and one for the right. If either side doesnt belong to the element whose handler
we are examining, it is set to None
a handler is made to act on one or any of the sides(chars), # or perhaps not care - zero width elements
so the sidedness of the handler, has to match the sidedness of the event in regard to the element
"""
#sidedness:
LEFT = 1
RIGHT = 2
#in addition to sdl key constants:
UNICODE = -1

class H(collections.namedtuple("Handler", 'mods key sidedness')):
	def __new__(cls, mods, key, sidedness=None):
		return tuple.__new__(cls, (mods, key, sidedness))

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


w.Text.keys = {H((), K_BACKSPACE, LEFT): w.Text.k_backspace,
			   H((), K_DELETE, RIGHT): w.Text.k_delete,
			   H((), UNICODE): w.Text.k_unicode}


def press(self, e):
	self.on_press.emit(self)
	return s.CHANGED

w.Button.press = press

w.Button.keys = {H((), (K_RETURN, K_SPACE)): w.Button.press}

w.NState.keys = {H((), (K_RETURN, K_SPACE)): w.NState.toggle}



"""
nodes.py
"""


def eval(s):
	s.eval()
	return CHANGED

def delete_self(s):
	s.parent.delete_child(s)
	return AST_CHANGED

n.Node.keys = odict({
	H((),           K_F7):      eval,
	H(KMOD_CTRL,    K_DELETE):  delete_self
})


n.Syntaxed.keys = n.Node.keys.updated({
	H(KMOD_CTRL, K_PERIOD): n.Syntaxed.prev_syntax,
    H(KMOD_CTRL, K_COMMA ): n.Syntaxed.next_syntax})


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

n.List.keys = n.List.__bases__[-1].keys.updated(
	{   H((KMOD_CTRL),  K_DELETE): (delete_item_check, delete_item),
		H((),           K_RETURN): newline})

def run_line(self, e):
	index = self.index_of_item_under_cursor(e)
	result = self.items[index].eval()
	result.parent = self
	self.items.insert(index + 1, result)
	return s.CHANGED

print(n.Statements.__bases__[-1])
n.Statements.keys = n.Statements.__bases__[-1].keys.updated(
	{H(KMOD_CTRL, K_RETURN): (n.Statements.have_item_under_cursor, run_line)})


n.Module.keys = n.Module.__bases__[-1].keys.update({
	H(KMOD_CTRL, K_s): n.Module.save,
	H(KMOD_CTRL, K_r): n.Module.reload,
	H(KMOD_CTRL, K_BACKSLASH ): n.Module.run})


n.ParserBase.keys = n.ParserBase.__bases__[-1].keys.updated({
	H((), K_BACKSPACE, LEFT): (n.ParserBase.check_backspace, n.ParserBase.k_backspace),
	H((), K_DELETE, LEFT): (n.ParserBase.check_backspace, n.ParserBase.k_delete)
	})






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

