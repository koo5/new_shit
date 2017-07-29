#from typing import Iterable

from weakref import ref as weakref
from types import GeneratorType
from collections import namedtuple
from pprint import pformat as pp

from lemon_utils.pizco_signal.util import Signal

#import sys
#sys.path.insert(0, 'fuzzywuzzy') #git version is needed for python3 (git submodule init; git submodule update)
from fuzzywuzzy import fuzz

from lemon_utils.lemon_six import iteritems, unicode
from lemon_args import args
from lemon_utils.utils import Evil, batch, clamp, flatten, odict
from lemon_colors import colors
from lemon_utils.dotdict import Dotdict

import logging
logger=logging.getLogger("root")
info=logger.info
log=logger.debug

import nodes
import palette
import mltt, lc

from tags import *
from element import Element, _collect_tags
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

	def on_elem_mouse_press(s, elem, button):
		pass


class Editor(ServerFrame):
	def __init__(s):
		super(Editor, s).__init__()

		s.root = nodes.make_root()
		if not args.kbdbg:
			lc.build_in_lc1(s.root)
			lc.build_in_lc2(s.root)
			lc.build_in_cube(s.root)
			mltt.build_in_MLTT(s.root)

		s.root.fix_parents()
		s.atts = Atts(dict(left={},right={},middle={}))
		s.on_serverside_change = Signal(1)
		s.on_atts_change = Signal(0)

	def changed_dude(s):
		s.root.changed = True
		s.signal_change(True)

	def on_elem_mouse_press(s, elem, button):
		if elem.on_mouse_press(button):
			s.root.changed = True
			s.signal_change()
			return True

	def signal_change(s, force=False):
		if force or s.root.changed or s.root.ast_changed:
			#s.on_serverside_change.emit(s.root.ast_changed)
			#log("s.draw_signal.emit()")
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
		editor.atts.any[Att.elem].module().run_line(editor.atts.any[Att.elem])
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


def handle_keypress(e):
	ph = potential_handlers(e.trip)
	log(e)
	for k, (elem, handler) in ph:
		#log("matching with %s:%s..", k, handler)
		if (
			(e.mods == k.mods and e.key == k.key)
		or
		    (k.key == UNICODE
		     and e.uni
		     and len(e.mods) == 0
		     and e.key not in (keys.K_ESCAPE, keys.K_BACKSPACE, keys.K_DELETE))):

				e.any = e.trip.middle or e.trip.left or e.trip.right

				e.left, e.middle, e.right = (
					e.trip.left   if e.trip.left and e.trip.left.get(Att.elem) == elem else None,
					e.trip.middle if e.trip.middle and e.trip.middle.get(Att.elem) == elem else None,
					e.trip.right  if e.trip.right and e.trip.right.get(Att.elem) == elem else None)

				e.atts = e.middle or e.left or e.right
				#this should be named "my", to reflect that is corresponds to the node thats gonna handle it,
				# not some of its children (as opposed to "any")

				log("match:%s.%s", elem, handler.func)
				return elem, handler.func(elem, e)


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
	def move(s, y):
		pass

class Menu(SidebarFrame):
	def __init__(s):
		super().__init__()
		s.editor = editor
		#editor.on_serverside_change.connect(s.on_editor_change)
		editor.on_atts_change.connect(s.update)
		s.valid_only = False
		s._changed = True
		nodes.m = s.marpa = ThreadedMarpa(send_thread_message, args.graph_grammar or args.log_parsing)
		thread_message_signal.connect(s.on_thread_message)
		s.parse_results = []
		s.palette_results = []
		s.sorted_everything = []
		s.current_text = "yo"
		s._current_parser_node = None
		s.must_update = True

	#weakref wrapper
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

	def on_editor_change(s, ast):
		s.must_update = True

	def update(s):
		node_changed = s.parser_changed()
		old_text = s.current_text
		s.update_current_text()
		if s.current_parser_node and (node_changed or old_text != s.current_text):
			s.update_menu()

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
			except AssertionError as e:
				print ("assertion error", e)
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

	def on_thread_message(s):
		m = s.marpa.t.output.get()
		if m.message == 'precomputed':
			#if m.for_node == s.current_parser_node:
				node = m.for_node()
				if node:#brainfart
					s.marpa.enqueue_parsing(s.parser_items2tokens(node))
		elif m.message == 'parsed':
				log (m.results)
				s.parse_results = [nodes.ParserMenuItem(['a parse'], x) for x in m.results]
				s.update_items()
				#	r.append(ParserMenuItem(i, 333))
				s.signal_change()

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
		text = ""
		if i != None:

			try:# we're gonna need to first re-project the editor,
				# then have the frontend call a more general editor.after-project, that updates
				# the atts and notifies the menu. We have outdated atts here now.

				if isinstance(parser.items[i], nodes.Node):
					text = ""
				else:
					text = parser.items[i].text
			except IndexError:
				pass

		s.current_text = text

	def create_palette(s, scope, atts, parser):
		log = logging.getLogger('menu').debug
		s.palette_results = []
		log("scope:%s"%len(scope))
		for x in scope:
			log("%s:"%x)
			a = palette.palette(x, scope, s.current_text, parser)
			s.palette_results += a
			for i in a:
				log(i.value.tostr())

		s.palette_results = flatten(s.palette_results)
		log("palette_results:%s"% len(s.palette_results))

		s.update_items()

	def update_items(s):
		log = logging.getLogger('menu').debug
		log("parse_results:%s"% len(s.parse_results))
		s.sorted_everything = s.sort_palette(s.palette_results + s.parse_results,
		                                     s.current_text, s.current_parser_node.type)
		log("sorted_everything:%s"% len(s.sorted_everything))

		s.current_parser_node.menu = s.sorted_everything
		"""
		log = logging.getLogger('menu').debug
		log("MENU:")
		for i in s.sorted_everything:
			log(i.value.tostr())
			for k,v in iteritems(i.scores._dict):
				log("%s:%s"%(k,v ))
			for v in i.notes:
				log(v)
			log("")
		"""
	@staticmethod
	def sort_palette(items, text, decl):
		assert type(text) == unicode

		#0-100
		matchf = fuzz.token_set_ratio

		if isinstance(decl, nodes.Exp):
			decl = decl.type

		def score_item(item):
			v = item.value

			name = None
			try:
				try:
					name = v.name
				except KeyError as e:
					pass
			except AttributeError:
				pass
			if type(name) == str:
				item.scores.name = name
				item.scores.name_matchf = matchf(name, text)

			assert type(v.decl.name) == str
			item.scores.declname_matchf =  matchf(v.decl.name, text)
			item.scores.declname = v.decl.name

			if item.value.decl.works_as(decl):
				item.scores.worksas = 30
			else:
				item.invalid = True

			#search thru syntaxes
			#if isinstance(v, Syntaxed):
			#	for i in v.syntax:
			#   		if isinstance(i, t):
			#			item.score += fuzz.partial_ratio(i.text, s.pyval)
			#search thru an actual rendering(including children)
			tags =     v.render()
			texts = [i for i in tags if type(i) == unicode]
			#print texts
			texttags = " ".join(texts)
			item.scores.texttags_matchf = matchf(texttags, text)
			item.scores.texttags = texttags
			if text in texttags:
				item.scores.text_in_texttags = 200
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
		       ] + s.sorted_everything


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

	def sel_and_accept(s):
		if s.sel < 0:
			s.sel = 0
		s.accept()

	def accept_and_run(s):
		if s.sel == -1:
			s.sel = 0

		if s.current_parser_node.menu_item_selected(s.items[s.sel], s.editor.atts):
			s.sel = -1
			s.scroll_lines = 0
			s.editor.changed_dude()
			s.signal_change()
			s.editor.run_line()
			s.editor.changed_dude()


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



class NodeInfo(StaticInfoFrame):
	def __init__(s, editor):
		super().__init__()
		s.editor = editor
		editor.on_atts_change.connect(s.on_editor_atts_change)
		s.items = []

	def on_editor_atts_change(s) -> None:
		s._changed = True
		log(s.editor.atts)
		s.items = list(handlers_info(s.editor.atts)) + ["\n"] + s.global_keys
		s.draw_signal.emit()

	def on_editor_change(s, _):
		s.on_editor_atts_change()


class NodeDebug(StaticInfoFrame):
	def __init__(s, editor):
		super().__init__()
		s.editor = editor
		editor.on_atts_change.connect(s.on_editor_atts_change)
		s.items = []

	def on_editor_change(s, _):
		s.on_editor_atts_change()

	def on_editor_atts_change(s) -> None:
		s._changed = True
		s.items = []
		s.xxx()
		s.draw_signal.emit()

	def xxx(s):
		s.items += ["left:", str(editor.atts.left)]
		s.items += ["middle:", str(editor.atts.middle)]
		s.items += ["right:", str(editor.atts.right)]
"""		uc = editor.under_cursor
		while uc != None:
			if isinstance(uc, nodes.FunctionCall):
				s.items.append(InfoItem(["target=", ElementTag(uc.target)]))
			uc = uc.parent
		uc = s.root.under_cursor
		while uc != None:
			s.items.append(InfoItem([
				str(s.root.cursor_c) + ":"+ str(s.root.cursor_r)+ ":" +
				uc.long__repr__()]))
			uc = uc.parent
"""

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
	global thread_message_signal, send_thread_message, logframe, intro, editor, menu, node_info, node_debug

	thread_message_signal, send_thread_message = thread_message_signal_, send_thread_message_

	logframe = Log()

	#intro = Intro()

	editor = Editor()

	menu = Menu()

	node_info = NodeInfo(editor)
	node_debug = NodeDebug(editor)


def element_click(element):
	return element.on_mouse_press(e)


def load(name):
	assert(isinstance(name, unicode))
	nodes.b_lemon_load_file(editor.root, name)
	editor.render()
	try_move_cursor(root.root['loaded program'])

