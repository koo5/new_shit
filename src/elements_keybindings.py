import collections

from keys import *
from tags import *

import nodes as n
import widgets as w

from element import CHANGED
from nodes import AST_CHANGED

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
		if type(mods) != tuple:
			mods = (mods, )
		return tuple.__new__(cls, (mods, key, sidedness))

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
	return CHANGED
w.Button.press = press

w.Button.keys = {H((), (K_RETURN, K_SPACE)): w.Button.press}




def toggle(self, e):
	self.value = self.value + 1
	if self.value == len(self.texts):
		self.value = 0
	log(self.value)
	self.on_change.emit(self)
w.NState.toggle = toggle

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


n.Syntaxed.keys = n.Node.keys.plus({
	H(KMOD_CTRL, K_PERIOD): n.Syntaxed.prev_syntax,
    H(KMOD_CTRL, K_COMMA ): n.Syntaxed.next_syntax})


def delete_item_check(s, atts):
	return s.item_index(atts) != None

def delete_item(s):
	ii = self.item_index(e)
	del self.items[ii]
	return CHANGED

def newline(s, e):
	item_index = s.item_index(e.atts)
	s.newline(item_index)
	return CHANGED

n.List.keys = n.List.__bases__[-1].keys.plus(
	{   H((KMOD_CTRL),  K_DELETE): (delete_item_check, delete_item),
		H((),           K_RETURN): (lambda s, atts: s.item_index(atts) != None, newline)})

def run_line(self, e):
	index = self.index_of_item_under_cursor(e)
	result = self.items[index].eval()
	result.parent = self
	self.items.insert(index + 1, result)
	return CHANGED

print(n.Statements.__bases__[-1])
n.Statements.keys = n.Statements.__bases__[-1].keys.plus(
	{H(KMOD_CTRL, K_RETURN): (lambda s, atts: s.item_index(atts) != None, run_line)})


n.Module.keys = n.Module.__bases__[-1].keys.plus({
	H(KMOD_CTRL, K_s): n.Module.save,
	H(KMOD_CTRL, K_r): n.Module.reload,
	H(KMOD_CTRL, K_BACKSLASH ): n.Module.run})


def check_backspace(s, atts):
	i = a.get(item_att)
	if i:
		return i[0] == s and s.items[i[1]]

def k_backspace(s):
	s.root.delayed_cursor_move -= 1
	s.on_edit.emit(s)
	return CHANGED


"""
analogically with delete,
both items will know not to handle it, so parser gets it,
so it must have a handler defined for between, or a checker, and
based on item_att delete(or deconstruct) the node
if Parser is empty: check succeeds only for UNICODE (on body), creates Text
"""


def k_delete(s):
	s.on_edit.emit(s)
	return CHANGED



n.ParserBase.keys = n.ParserBase.__bases__[-1].keys.plus({
	H((), K_BACKSPACE, LEFT): (check_backspace, k_backspace),
	H((), K_DELETE, LEFT): k_delete
	})

