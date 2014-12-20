from types import GeneratorType
from itertools import *
#from types import NoneType
from collections import namedtuple
from pizco import Signal

from lemon_utils.lemon_six import iteritems, unicode
from lemon_args import args
from lemon_utils.utils import Evil, batch
from lemon_colors import color, colors
from lemon_utils.lemon_logging import log

import nodes
from tags import *
from element import Element
from menu_items import InfoItem
import widgets
import elements_keybindings
import graph


class ServerFrame(object):
	"""base class for the server halves of frames"""
	def __init__(s):
		s.on_change = Signal(0)

	def signal_change(s):
		s.on_change.fire()

	def collect_tags(s):
		return batch(_collect_tags(s, s.tags()))

	@property
	def changed(s):
		return s.




class Editor(ServerFrame):
	def __init__(self):
		super(Editor, self).__init__()

		self.root = nodes.make_root()
		self.root.fix_parents()
		self.atts = {}

	def must_recollect(s):
		if s.root.changed:
			s.root.changed = False
			return True


	@property
	def element_under_cursor(s):
		"""we shouldnt need this if atts are in event, but it makes it possible
		to call things like run_line without passing it the event too.
		Ofc, this has to be kept updated from the client
		"""
		return s.atts.get(node_att)


	def tags(s):
		return s.root.tags()

	def get_delayed_cursor_move(editor):
		return editor.root.delayed_cursor_move

	def set_atts(editor, atts):
		assert type(atts) == dict
		log("setting atts under cursor:%s",atts)
		editor.atts = atts

	def run_active_program(editor):
		editor.root['some program'].run()

	def run_line(editor):
		editor.atts[node_att].module.run_line(editor.atts[node_att])

	def clear(editor):
		editor.root['some program'].clear()

	def	dump_root_to_file(editor):
		pass

	@property
	def changed(s):
		return s.root.changed

	def get_changed_and_clean(s):
		if s.changed:
			s.root.changed = False
			return True

def event_handled():
	for f in editor, logframe, menu:
		if f.changed:
			f.on_change.fire()
	for f in editor, logframe, menu:
		if f.changed:
			f.draw_signal.fire()


def element_keypress(event):
	event.atts = namedtuple('attributes', 'left middle right')(editor.atts)

	r = handle_keypress(event)

	if r:
		elem, handler_result = r
		if handler_result:
			module = elem.module
			if module:
				#event.final_root_state = deepcopy(editor.root) #for undo and redo. todo.
				log('history.append(event)')

		event_handled()


def handle_keypress(event):
	for side in [1,0,2]: #middle, left, right
		atts = e.orig_atts[side]
		if atts != None:
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



editor = Editor()


class Menu(ServerFrame):
	def __init__(s):
		super(Menu, s).__init__()
		s.editor = editor
		editor.on_change.connect(s.on_editor_change)
		s.valid_only = False
		s.items = []
		s.sel = 0

	def on_editor_change(s):
		log('recalculating...')
		#talk to nodes, marpa and fuzzywuzzy

	def marpa_callback(s):
		s._changed = True
		s.on_change.fire()
		s.draw_signal.fire()

	@property
	def changed(s):
		return s._changed
	def get_changed_and_clean(s):
		if s.changed:
			s._changed = False
			return True

	def tags(s):
		yield [ColorTag("fg"), "menu:\n"]
		for i in s.generate_items():
			yield [ElementTag(i)]
		yield EndTag()

	def generate_items(s):
		s.items = []
		e = s.element = s.editor.element_under_cursor
		if e != None:
			for i in e.menu(s.editor.atts):
				if not s.valid_only or i.valid: # move this check to nodes...or..lets have it in both places!
					s.items.append(i)
					yield i

	def accept(menu, idx):
		return menu.element.menu_item_selected(menu.items[idx], menu.root.atts)

	def toggle_valid(s):
		s.valid_only = not s.valid_only
		s.signal_change()



	def menu_dump(s):
		e = s.element = s.root.under_cursor
		atts = s.root.atts
		if e != None:
			e.menu(atts, True)


	def accept(self):
		if len(self.items_on_screen) > self.sel:
			if self.element.menu_item_selected(self.items_on_screen[self.sel], self.root.atts):
				self.sel = 0
				self.scroll_lines = 0
				return True


	def move(self, y):
		self.sel += y
		self.clamp_sel()



menu = Menu()




class StaticInfoFrame(ServerFrame):
	def __init__(s):
		super(StaticInfoFrame, s).__init__()
		s.name = s.__class__.__name__

	def tags(s):
		yield [ColorTag("help"), s.name + ":  "+"\n"]
		for i in s.items:
			yield [i, "\n"]
		yield [EndTag()] # color


class GlobalKeys(StaticInfoFrame):
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

"""
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
"""

class Intro(StaticInfoFrame):
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

intro = Intro()


class Log(ServerFrame):
	def __init__(s):
		super(Log, s).__init__()
		s.items = []
		s.on_add = Signal(1)
		s._dirty = True

	def add(s, msg):
		#timestamp, topics, text = msg
		#if type(text) != unicode:
		s.items.append(str(msg))
		print(str(msg))
		s.on_add.emit(msg) #
		s._dirty = True

	def is_dirty(s):
		return s._dirty

logframe = Log()



def element_click(element):
	return element.on_mouse_press(e)






def after_start():
	if args.load:
		load(args.load)

	if args.run:
		load(args.run)
		root.root['loaded program'].run()

	initially_position_cursor()

def initially_position_cursor():
	root.render()

	try:
		#if args.lesh:
		#	something = root.root['lesh'].command_line
		#else:
		something = root.root['some program'].ch.statements.items[1]

		root.cursor_c, root.cursor_r = project.find(something, root.lines)
		#root.cursor_c += 1
	except Exception as e:
		log (e.__repr__(), ", cant set initial cursor position")

def load(name):
	assert(isinstance(name, unicode))
	nodes.b_lemon_load_file(editor.root, name)
	editor.render()
	try_move_cursor(root.root['loaded program'])




on_change = Signal()

log(list(menu.collect_tags()))



def _collect_tags(elem, tags):
	for tag in tags:
		if type(tag) in (GeneratorType, list):
			for i in _collect_tags(elem, tag):
				yield i

		elif type(tag) == TextTag:
			yield tag.text

		elif type(tag) == ChildTag:
			e = elem.ch[tag.name]
			for i in _collect_tags(e, e.tags()):
				yield i

		elif type(tag) == MemberTag:
			e = elem.__dict__[tag.name] #get the element as an attribute #i think this should be getattr, but it seems to work
			for i in _collect_tags(e, e.tags()):
				yield i

		elif type(tag) == ElementTag:
			e = tag.element
			for i in _collect_tags(e, e.tags()):
				yield i

		else:
			yield tag


