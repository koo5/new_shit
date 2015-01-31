#from typing import Iterable

from weakref import ref as weakref
from types import GeneratorType
from collections import namedtuple
from pprint import pformat as pp

from lemon_utils.pizco_signal.util import Signal
from fuzzywuzzy import fuzz

from lemon_utils.lemon_six import iteritems, unicode
from lemon_args import args
from lemon_utils.utils import Evil, batch, clamp, flatten, odict
from lemon_colors import colors
from lemon_utils.lemon_logging import log
from lemon_utils.dotdict import Dotdict

import nodes
from tags import *
from element import Element
from menu_items import InfoItem
import widgets
import elements_keybindings
from elements_keybindings import LEFT, RIGHT, UNICODE
import keys

from marpa_cffi.marpa_rpc_client import ThreadedMarpa



class Atts(object):
	def __init__(s, a) -> int:
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
		self.on_atts_change = Signal(0)

	def signal_change(s, force=False):
		if force or s.root.changed or s.root.ast_changed:
			s.on_serverside_change.emit(s.root.ast_changed)
		log("s.draw_signal.emit()")
		s.draw_signal.emit()

	def must_recollect(s):
		#log('must_recollect(%s)', s)
		if s.root.changed or s.root.ast_changed:
			s.root.changed = s.root.ast_changed = False
			#log("true")
			return True
		#log("false")

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
		editor.on_atts_change.emit()
		#editor.draw_signal.emit()

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
	log(event)
	for k, (elem, handler) in ph:
		log("matching with %s:%s..", k, handler)
		if (event.mods == k.mods and (
			event.key == k.key ) or
		    (k.key == UNICODE and event.uni and event.key not in (
		    keys.K_ESCAPE, keys.K_BACKSPACE, keys.K_DELETE))):

				event.any = event.trip.middle or event.trip.left or event.trip.right
				event.left, event.middle, event.right = (
					event.trip.left   if event.trip.left and event.trip.left.get(Att.elem) == elem else None,
					event.trip.middle if event.trip.middle and event.trip.middle.get(Att.elem) == elem else None,
					event.trip.right  if event.trip.right and event.trip.right.get(Att.elem) == elem else None)
				event.atts = event.middle or event.left or event.right

				log("match:%s.%s", elem, handler.func)
				return elem, handler.func(elem, event)


def potential_handlers(trip):
	"""return every handler for the elements in trip and parents, whose checker passess.
	mods and key are irrelevant, we arent dealing with any particular event
	"""
	output = odict()

	elems = [x.get(Att.elem) for x in [trip.middle or {}, trip.left or {}, trip.right or {}]]

	while any(elems):
		for elem, sidedness, atts in [
								(elems[0], None, trip.middle),
		                        (elems[1], LEFT, trip.left),
								(elems[2], RIGHT, trip.right)]:
			if elem:
				for keys, handler in iteritems(elem.keys):
					if handler.sidedness in (None, sidedness):
						if not handler.checker or handler.checker(elem, atts):
							if keys not in output:
								yield keys, (elem, handler)
								output[keys] = True
		for i in range(3):
			if elems[i]:
				elems[i] =  elems[i].parent


def handlers_info(trip):

	for k, (elem, handler) in potential_handlers(trip):

		element_name = elem.__class__.__name__
		function_name = handler.func.__name__

		if k.key == UNICODE:
			kstr = 'text input'
		else:
			kstr = key_to_name(k.key)
		kmods = mods_to_str(k.mods)
		yield ' '.join(kmods + [kstr]) + ": " + element_name + "." + function_name


	"""

	for sidedness, atts in [(None, trip.middle),
	             (elements_keybindings.LEFT, trip.left),
	             (elements_keybindings.RIGHT, trip.right)]:
		if atts != None:
			elem = atts.get(Att.elem)
			if elem:
				#log((elem, elem.keys))
				for handler, v in iteritems(elem.keys):
					#log((handler, v, elem, elem.keys))
					if	handler.sidedness in (None, sidedness):
						if type(v) == tuple:
							checker, func = v
						else:
							checker, func = None, v
						if not checker or checker(elem,atts):
							yield elem, handler, func
	"""

class SidebarFrame(ServerFrame):
	def __init__(s):
		super().__init__()
		s.sel = -1


class Menu(SidebarFrame):
	def __init__(s):
		super().__init__()
		s.editor = editor
		editor.on_serverside_change.connect(s.on_editor_change)
		editor.on_atts_change.connect(s.on_editor_atts_change)
		s.valid_only = False
		s._changed = True
		nodes.m = s.marpa = ThreadedMarpa(send_thread_message, args.graph_grammar or args.log_parsing)
		thread_message_signal.connect(s.on_thread_message)
		s.parse_results = []
		s.sorted_palette = []
		s.current_text = "yo"
		s._current_parser_node = None

	@property
	def current_parser_node(s):
		if s._current_parser_node:
			return s._current_parser_node()
	@current_parser_node.setter
	def current_parser_node(s, x):
		s._current_parser_node = weakref(x)




	def must_recollect(s):
		if s._changed:
			s._changed = False
			return True

	def on_editor_change(self, ast):
		#welp, changes tracking is tbd..
		_ = self.parser_changed()
		if self.current_parser_node:
			self.update_menu()

	def on_editor_atts_change(self):
		if self.parser_changed():
			self.update_menu()

	def parser_changed(s):
		def relevant_parser(e):
			if not e:
				return None
			for i in [e] + e.ancestors:
				if isinstance(i, nodes.Parser):
					return i

		e = relevant_parser(s.editor.element_under_cursor)

		if e and e != s.current_parser_node:
			s.current_parser_node = e
			return True

	def update_menu(s):
		if s.current_parser_node:
			try:#hack, current_parser_node could have been deleted,
				#and theres currently no way to know
				scope = s.current_parser_node.scope()
			except AssertionError:
				return
			s.update_current_text()
			s.prepare_grammar(scope)
			s.create_palette(scope, s.editor.atts, s.current_parser_node)
			s.signal_change()

	def prepare_grammar(s, scope):
		#s.marpa.t.input.clear()
		log("prepare grammar..")
		for i in s.editor.root.flatten():
			i.forget_symbols() # todo:start using visitors
		s.marpa.collect_grammar(scope)
		assert s.current_parser_node
		s.marpa.enqueue_precomputation(weakref(s.current_parser_node))

	def on_thread_message(self):
		m = self.marpa.t.output.get()
		if m.message == 'precomputed':
			#if m.for_node == self.current_parser_node:
				node = m.for_node()
				if node:#brainfart
					self.marpa.enqueue_parsing(self.parser_items2tokens(node))
		elif m.message == 'parsed':
				self.parse_results = [nodes.ParserMenuItem(x) for x in m.results]
				#	r.append(ParserMenuItem(i, 333))
				self.signal_change()

	@staticmethod
	def parser_node_item(parser, atts):
		try:
			parser_node, item_index = atts.any[Att.item_index]
		except KeyError:
			return None
		if parser == parser_node:
			return item_index

	def update_current_text(s):
		parser = s.current_parser_node
		i = s.parser_node_item(parser, s.editor.atts)

		if i == None:
			text = ""
		else:
			if isinstance(parser.items[i], nodes.Node):
				text = ""
			else:
				text = parser.items[i].text

		s.current_text = text

	def create_palette(s, scope, atts, parser):
		palette = flatten([x.palette(scope, s.current_text, parser) for x in scope])
		s.sorted_palette = s.sort_palette(palette, s.current_text, s.current_parser_node.type)

	@staticmethod
	def sort_palette(items, text, decl):
		matchf = fuzz.token_set_ratio#partial_ratio

		if isinstance(decl, nodes.Exp):
			decl = decl.type

		def score_item(item):
			v = item.value
			assert type(text) == unicode
			try:
				#assert type(v.name) == unicode,  v.name
				item.scores.name = matchf(unicode(v.name), text, False), v.name #0-100
			except AttributeError as e:
				# no name
				pass

			assert type(v.decl.name) == unicode
			item.scores.declname = 3 * matchf(v.decl.name, text, False), v.decl.name #0-100

			if item.value.decl.works_as(decl):
				item.scores.worksas = 200
			else:
				item.invalid = True

			#search thru syntaxes
			#if isinstance(v, Syntaxed):
			#	for i in v.syntax:
			#   		if isinstance(i, t):
			#			item.score += fuzz.partial_ratio(i.text, self.pyval)
			#search thru an actual rendering(including children)
			tags =     v.render()
			texts = [i for i in tags if type(i) == unicode]
			#print texts
			texttags = " ".join(texts)
			item.scores.texttags = matchf(texttags, text), texttags
			return item

		return sorted(map(score_item, items), key=lambda i: -i.score)



	"""
	def generate_items(s):
		s.items = []
		e = s.element = s.editor.element_under_cursor
		if e != None:
			for i in e.menu(s.editor.atts):
				if not s.valid_only or i.valid: # move this check to nodes...or..lets have it in both places!
					s.items.append(i)
					yield i
	"""

	@property
	def items(s):
		return [#nodes.DefaultParserMenuItem(s.current_text)
		       ] + s.parse_results + s.sorted_palette


	def get_items(s):
		for i in s.items:
			yield _collect_tags(666, [ColorTag(colors.fg), ElementTag(i)])


	def parser_items2tokens(s, items):
		symbols, text = [], ""
		for i in items:
			if isinstance(i, widgets.Text):
				symbols.extend(s.marpa.string2tokens(i.text))
				text += i.text
			else:
				symbols.append(i.symbol)
				text += "X"
		return symbols, text

	def signal_change(s):
		s._changed = True
		s.draw_signal.emit()

	def tags4item(s, i: int) -> list:
		return _collect_tags(666, [ColorTag(colors.fg), AttTag(Att.item_index, (s, i)),  ElementTag(s.items[i]), EndTag(), EndTag()])

	"""
	def tags(s):
		yield [ColorTag(colors.fg)]

		#yield [AttTag(Att.item_index, (s, -1))]
		yield ["menu:(%s items)\n"%len(s.parse_results)]
		#yield [EndTag()]

		for index, item in enumerate(s.items):
			yield [AttTag(Att.item_index, (s, index)),  ElementTag(item), EndTag(), "\n"]

		yield ["---", EndTag()]
	"""
	def toggle_valid(s):
		s.valid_only = not s.valid_only
		s.signal_change()

	def menu_dump(s):
		e = s.element = s.root.under_cursor
		atts = s.root.atts
		if e != None:
			e.menu(atts, True)


	def accept(s):
		if s.sel >= 0:
			if s.current_parser_node.menu_item_selected(s.items[s.sel], s.editor.atts):
				s.sel = -1
				s.scroll_lines = 0
				s.editor.root.ast_changed = True
				s.editor.signal_change()
				s.signal_change()
				return True


	def move(s, y):
		s.sel = clamp(s.sel + y, -1, len(s.items))
		s.signal_change()



class StaticInfoFrame(SidebarFrame):
	def __init__(s):
		super().__init__()
		s.name = s.__class__.__name__
		s._changed = True

	def get_items(s):
		for i in s.items:
			yield [ColorTag(colors.help), TextTag(i)]

	def must_recollect(s):
		if s._changed:
			s._changed = False
			return True


class GlobalKeys(StaticInfoFrame):
	items = ["ctrl + =,- : font size",
			"f5 : eval",
			"f4 : clear eval results",
			"f2 : replay previous session",
			"ctrl + up, down: menu movement",
			"space: menu selection",
	        #"ctrl + d : dump root frame to dump.txt",
	        #"ctrl + p : dump parents",
	        #"ctrl + g : generate graph.gif",
			#"f9 : only valid items in menu - doesnt do much atm",
			#"f8 : toggle the silly arrows from Refs to their targets, (and current node highlighting, oops)"
			]


class NodeInfo(StaticInfoFrame):
	def __init__(s, editor):
		super().__init__()
		s.editor = editor
		editor.on_serverside_change.connect(s.on_editor_change)
		editor.on_atts_change.connect(s.on_editor_atts_change)
		s.items = []
		#s.global_keys = []

	def on_editor_atts_change(self) -> None:
		self._changed = True
		log(self.editor.atts)
		self.items = list(handlers_info(self.editor.atts)) + ["\n"] + self.global_keys
		self.draw_signal.emit()

	def on_editor_change(self, _):
		self.on_editor_atts_change()

"""
	def xxx(s):

		uc = editor.under_cursor
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


def init(thread_message_signal_, send_thread_message_):
	global thread_message_signal, send_thread_message, logframe, intro, editor, menu, node_info

	thread_message_signal, send_thread_message = thread_message_signal_, send_thread_message_

	logframe = Log()

	intro = Intro()

	editor = Editor()

	menu = Menu()

	node_info = NodeInfo(editor)


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
	"""make a flat list, expanding child elements"""
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


