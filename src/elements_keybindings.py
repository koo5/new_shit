import collections
from pprint import pformat as pp

from keys import *
from tags import *

import nodes as n
import widgets as w

from element import CHANGED
from nodes import AST_CHANGED

from lemon_utils.utils import odict
from lemon_utils.lemon_logging import log
from lemon_utils.lemon_six import iteritems

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

class K(collections.namedtuple("Keys", 'mods key')):
	def __new__(cls, mods, key):
		if type(mods) == tuple:
			mods = frozenset(mods)
		elif type(mods) == frozenset:
			pass
		else:
			mods = frozenset([mods])
		return tuple.__new__(cls, (mods, key))

class H(collections.namedtuple("Handler", 'func checker sidedness')):
	def __new__(cls, func, checker=None, sidedness=None):
		return tuple.__new__(cls, (func, checker, sidedness))

def add_keys(node, sup, handlers):
	if sup == -1:
		node.keys = node.__bases__[-1].keys.copy()
	elif sup == None:
		node.keys = odict()
	else:
		node.keys = sup.keys.copy()



	for k, v in iteritems(handlers):
		if type(k.key) == tuple:
			for key in k.key:
				node.keys[K(k.mods, key)] = v
		else:
			node.keys[k] = v

"""
widgets.py
"""
add_keys(w.Widget, None, {})

def k_backspace (s, e):
	pos = e.left[Att.char_index]
	s.text = s.text[0:pos] + s.text[pos+1:]
	return s.after_edit(-1)
w.Text.k_backspace = k_backspace

def k_delete(s, e):
	pos = e.right[Att.char_index]
	s.text = s.text[0:pos] + s.text[pos+1:]
	return s.after_edit(0)
w.Text.k_delete = k_delete

def k_unicode(s, e):
	atts = e.atts
	pos = atts[Att.char_index]
	s.text = s.text[:pos] + e.uni + s.text[pos:]
	return s.after_edit(len(e.uni))
w.Text.k_unicode = k_unicode

add_keys(w.Text, None,
			{
			K((), K_BACKSPACE):  H(w.Text.k_backspace, None, LEFT),
			K((), K_DELETE):     H(w.Text.k_delete, None, RIGHT),
			K((), UNICODE):      H(w.Text.k_unicode)})




def press(self, e):
	self.on_press.emit(self)

add_keys(w.Button, None, {
	K((), (K_RETURN, K_SPACE)): H(press)})




def toggle(self, e):
	self.value = self.value + 1
	if self.value == len(self.texts):
		self.value = 0
	log(self.value)
	self.on_change.emit(self)
w.NState.toggle = toggle

add_keys(w.NState, None, {
	K((), (K_RETURN, K_SPACE)): H(w.NState.toggle)})




def toggle(self):
	self.value = not self.value
	self.on_change.emit(self)
add_keys(w.Toggle, None, {
	K((), (K_RETURN, K_SPACE)): H(toggle)})




"""
nodes.py
"""


def eval(s, e):
	s.eval()
	return CHANGED


#def delete_self_check(s, atts):
#	return s.parent != None

def delete_self(s, e):
	s.parent.delete_child(s)
	return AST_CHANGED

add_keys(n.Node, None, {
	K((),           K_F7):      H(eval),
	K(KMOD_CTRL,    K_DELETE):  H(delete_self)
})

add_keys(n.Root, None, {})


def prev_syntax(s, e):
	s.prev_syntax()
def next_syntax(s, e):
	s.next_syntax()

add_keys(n.Syntaxed, n.Node, {
	K(KMOD_CTRL, K_PERIOD): H(prev_syntax),
    K(KMOD_CTRL, K_COMMA ): H(next_syntax)})


def delete_item_check(s, atts):
	return s.item_index(atts) != None

def delete_item(s):
	ii = self.item_index(e)
	del self.items[ii]
	return CHANGED

def newline(s, e):
	log("eee")
	log(pp(e))
	item_index = s.item_index(e.atts)
	s.newline(item_index)
	return CHANGED

add_keys(n.List, -1,
	{   K(KMOD_CTRL,    K_DELETE): H(delete_item, delete_item_check),
		K((),           K_RETURN): H(newline, lambda s, atts: s.item_index(atts) != None)})

def run_line(self, e):
	index = self.index_of_item_under_cursor(e)
	result = self.items[index].eval()
	result.parent = self
	self.items.insert(index + 1, result)
	return CHANGED

add_keys(n.Statements, -1, {
	K(KMOD_CTRL, K_RETURN): H(run_line, lambda s, atts: s.item_index(atts) != None)})


def save(s, e):
	s.save()
def reload(s, e):
	s.reload()

add_keys(n.Module, -1, {
	K(KMOD_CTRL, K_s): H(save),
	K(KMOD_CTRL, K_r): H(reload),
	K(KMOD_CTRL, K_BACKSLASH ): H(n.Module.run)})


def check_backspace(s, atts):
	i = atts.get(Att)
	if i != None:
		return i[0] == s# and s.items[i[1]]

def k_backspace(s):
	s.root.delayed_cursor_move.chars -= 1
	s.on_edit.emit(s)
	return CHANGED

def k_delete(s):
	s.on_edit.emit(s)
	return CHANGED

def k_unicode(s, e):
	atts = e.atts
	log("adding first item")
	s.items.append(w.Text(s, e.uni))
	s.root.delayed_cursor_move.node = s.items[0]
	s.root.delayed_cursor_move.chars = len(e.uni)

def k_unicode_check(s, _):
	return len(s.items) == 0

add_keys(n.ParserBase, -1, {
	#H((), K_BACKSPACE, LEFT): (check_backspace, k_backspace),
	#H((), K_DELETE, LEFT): k_delete
	K((), UNICODE): H(k_unicode, k_unicode_check)

	})

"""
analogically with delete,
both items will know not to handle it, so parser gets it,
so it must have a handler defined for between, or a checker, and
based on item_att delete(or deconstruct) the node
if Parser is empty: check succeeds only for UNICODE (on body), creates Text
"""

