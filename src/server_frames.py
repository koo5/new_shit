from types import GeneratorType
from collections import namedtuple
from pprint import pformat as pp

from pizco import Signal

from lemon_utils.lemon_six import iteritems, unicode
from lemon_args import args
from lemon_utils.utils import Evil, batch
from lemon_colors import colors
from lemon_utils.lemon_logging import log
from lemon_utils.dotdict import Dotdict

import nodes
from tags import *
from element import Element
from menu_items import InfoItem
import widgets
import elements_keybindings
import keys

from marpa_cffi.marpa_rpc_client import ThreadedMarpa

class Atts(object):
	def __init__(s, a):
		#s.by_priority = [a['middle'], a['left'], a['right']]
		s.middle, s.left, s.right = a['middle'], a['left'], a['right']
		s.any = s.middle or s.left or s.right or {}
		# umm we could make a key to cycle the any if needed

class ServerFrame(object):
	"""base class for the server parts of frames"""
	def __init__(s):
		s.draw_signal = Signal(0)

	def collect_tags(s):
		return batch(_collect_tags(s, s.tags()))


class Editor(ServerFrame):
	def __init__(self):
		super(Editor, self).__init__()

		self.root = nodes.make_root()
		self.root.fix_parents()
		self.atts = Atts(dict(left={},right={},middle={}))
		self.on_serverside_change = Signal(1)

	def signal_change(s, force=False):
		if force or s.root.changed or s.root.ast_changed:
			s.on_serverside_change.emit(s.root.ast_changed)
		log("s.draw_signal.emit()")
		s.draw_signal.emit()

	def must_recollect(s):
		log('must_recollect(%s)', s)
		if s.root.changed or s.root.ast_changed:
			s.root.changed = s.root.ast_changed = False
			log("true")
			return True
		log("false")

	@property
	def element_under_cursor(s):
		return s.atts.any.get(Att.elem)

	def tags(s):
		return s.root.tags()

	def get_delayed_cursor_move(editor):
		return editor.root.delayed_cursor_move

	def set_atts(editor, atts):
		log("setting atts under cursor to %s",pp(atts))
		editor.atts = Atts(atts)
		editor.signal_change(True)

	def run_active_program(editor):
		editor.root['some program'].run()
		editor.signal_change()

	def run_line(editor):
		editor.atts.any[Att.elem].module.run_line(editor.atts.any[Att.elem])
		editor.signal_change()

	def clear(editor):
		editor.root['some program'].clear()
		editor.signal_change()

	def	dump_root_to_file(editor):
		pass

	def keypress(s, event):
		"""
		event handling is in its second iteration. i introduced the left/middle/right
		system and checkers, there will be undo/redo, context-sensitive action list.
		this is a rewrite building on previous experience,
		but the actual implementation is hackish, as i only have it figured out conceptually,
		not down to the code level
		"""
		event.trip = editor.atts

		r = handle_keypress(event)

		if r:
			elem, handler_result = r
			#if handler_result:
				#module = elem.module
				#if module:
					#event.final_root_state = deepcopy(editor.root) #for undo and redo. todo.
					#log('history.append(%s)..',event)
			s.root.changed = True
			s.signal_change()


def handle_keypress(event):
	ph = potential_handlers(event.trip)
#	log(pp(list(ph)))
	log(event)
	for elem, handler, func in ph:
		log("matching with %s..", handler)
		if (event.mods == set(handler.mods) and (
			event.key == handler.key or (type(handler.key) == tuple and	event.key in handler.key)) or
		    (event.uni and handler.key == elements_keybindings.UNICODE and event.key not in (keys.K_ESCAPE, ))):
				event.left, event.middle, event.right = (
					event.trip.left   if event.trip.left and event.trip.left.get(Att.elem) == elem else None,
					event.trip.middle if event.trip.middle and event.trip.middle.get(Att.elem) == elem else None,
					event.trip.right  if event.trip.right and event.trip.right.get(Att.elem) == elem else None)
				event.atts = event.middle or event.left or event.right
				log("match:%s.%s",elem,func)
				return elem, func(elem, event)



def potential_handlers(trip):
	"""return every handler for the element in atts, whose checker passess.
	mods and key are irrelevant, we arent dealing with any particular event

	its counterintuitive that we first list all potential handlers(running their checker)
	and only then look for a match of mod and key
	"""
	for sidedness, atts in [(None, trip.middle),
	             (elements_keybindings.LEFT, trip.left),
	             (elements_keybindings.RIGHT, trip.right)]:
		if atts != None:
			elem = atts.get(Att.elem)
			if elem:
				log((elem, elem.keys))
				for handler, v in iteritems(elem.keys):
					#log((handler, v, elem, elem.keys))
					if	handler.sidedness in (None, sidedness):
						if type(v) == tuple:
							checker, func = v
						else:
							checker, func = None, v
						if not checker or checker(elem,atts):
							yield elem, handler, func


editor = Editor()


class Menu(ServerFrame):
	def __init__(s):
		super(Menu, s).__init__()
		s.editor = editor
		editor.on_serverside_change.connect(s.on_editor_change)
		s.valid_only = False
		s._changed = True
		s.parser_node = None
		s.items = []
		s.sel = 0
		nodes.m = s.marpa = ThreadedMarpa(args.graph_grammar or args.log_parsing)

	def must_recollect(s):
		if s._changed:
			s._changed = False
			return True

	def on_editor_change(self, ast):
		if ast:
			self.prepare_grammar()

	def on_editor_element_change(s):
		if s.parser_changed():
			s.prepare_grammar()

	def parser_changed(s):
		e = s.editor.element_under_cursor
		for i in e.ancestors:
			if isinstance(i, nodes.Parser):
				if i != s.parser_node:
					s.parser_node = e
					return True

	def prepare_grammar(s):
		s.marpa.input.clear()
		s.marpa.collect_grammar(s.editor.root, s.editor.element_under_cursor)
		s.marpa.queue_precomputation()

	def on_thread_message(s):
		m = s.marpa.output.get()
		if m.message == 'precomputed':
			if m.for_node == s.parser_node:
				s.marpa.queue_parsing(s.parser_items2tokens(s.parser_node.items))
		elif m.message == 'parsed':
				s.parse_results = m.results


	def parser_items2tokens(s, items):
		r = []
		for i in items:
			if type(i) == unicode:
				r.extend(s.string2tokens(i))
			else:
				r.append(i.symbol)





		log("possibly check against cached atts/text, then call marpa")
		#self._changed = True

	def marpa_callback(s):
		s._changed = True
		s.on_change.fire()
		s.draw_signal.fire()

	def tags(s):
		yield [ColorTag(colors.fg), "menu:\n"]
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


	def update_items(s):
		s.items = (
			[DefaultParserMenuItem(text)]+
			[s.parse_results]+
			[s.sorted_palette])



	def toggle_valid(s):
		s.valid_only = not s.valid_only
		s.signal_change()



	def menu_dump(s):
		e = s.element = s.root.under_cursor
		atts = s.root.atts
		if e != None:
			e.menu(atts, True)


	def accept(menu, idx):
		return menu.element.menu_item_selected(menu.items[idx], menu.root.atts)
	def accept(self):
		return False
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


	def must_recollect(s):
		if s._dirty:
			s._dirty = False
			return True

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


