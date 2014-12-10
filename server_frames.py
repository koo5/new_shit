from pizco import Signal

import graph

import lemon_platform as platform
from lemon_colors import color, colors

import nodes
from element import Element
from menu_items import InfoItem
from tags import TextTag, ElementTag, MemberTag, ColorTag, EndTag, AttTag
import widgets
from lemon_utils.lemon_logging import log

from lemon_utils.lemon_six import iteritems, unicode
from lemon_args import args
from lemon_utils.utils import evil
from tags import proxy_this


import elements_keybindings


from pizco import Signal

class ServerFrame(object):

	def __init__(s):
		pass


class Editor(ServerFrame):
	def __init__(self):
		super(Editor, self).__init__()

		self.root = nodes.make_root()
		self.root.fix_parents()

		self.on_root_change = Signal()

	def tags(s):
		return s.root.tags()

	@property
	def element_under_cursor(s):
		"""we shouldnt need this if atts are in event, but it makes it possible
		to call things like run_line without passing it the event too.
		Ofc, this has to be kept updated from the client
		"""
		return s.atts[att_node]

	def set_atts(editor, atts):
		assert type(atts) == dict
		editor.atts = atts

	def run_active_program(editor):
		editor.root['some program'].run()

	def run_line(editor):
		editor.atts[node_att].module.run_line(editor.atts[node_att])

	def clear(editor):
		editor.root['some program'].clear()

	def	dump_root_to_file(editor):
		pass

	def get_delayed_cursor_move(editor):
		return editor.root.delayed_cursor_move


editor = Editor()


class Menu(ServerFrame):
	def __init__(s, root):
		super(Menu, s).__init__()
		s.editor = editor
		s.valid_only = False
		s.items = []

	def tags(s):
		yield ColorTag("fg")
		for i in s.generate_palette():
			yield [ElementTag(i)]
		yield EndTag()


menu = Menu(editor)


def menu_generate_items():
	s=menu
	s.items = []
	e = s.element = s.root.element_under_cursor
	if e != None:
		for i in e.menu(s.root.atts):
			if not s.valid_only or i.valid: # move this check to nodes...or..lets have it in both places!
				s.items.append(i)
				yield i

def menu_accept(idx):
	return menu.element.menu_item_selected(menu.items[idx], menu.root.atts)

def menu_toggle_valid():
	menu.valid_only = not menu.valid_only




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
proxied_intro = proxy_this(intro)


class Log(ServerFrame):
	def __init__(s):
		super(Log, s).__init__()
		s.items = []
		s.on_add = Signal(1)

	def add(s, msg):
		#timestamp, topics, text = msg
		#if type(text) != unicode:
		s.items.append(str(msg))
		print(str(msg))
		s.on_add.emit(msg)

log = Log()



def element_click(proxied_element):
	return deproxy(proxied_element).on_mouse_press(e)

def element_keypress(event):
	#for now, always talk to the element to the right of the cursor,
	# left is [0], right is [1]
	right = event.atts[1]
	if type(right) == dict and tags.att_node in right:
		element_id = right[tags.att_node]
		element = tags.proxied[element_id]

	#old style
	while element != None:
		assert isinstance(element, Element), (assold, element)
		if element.on_keypress(event):
			break
		assold = element
		element = element.parent


	if element != None:
	# the loop didnt end with root.parent, so some element must have handled it
		if args.log_events:
			log("handled by "+str(element))
			return True



after_event = Signal()



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




"""
general ways that rpcing complicates things;

have to do more effort at proper mvc-y eventing, This would in some form be
necessary for best performance anyway (keeping track of dirtiness at various levels.
But the split between the server and client part of frames isnt nice..

proxying elements: wont be a performance hit, if it will, it can be easily stubbed
proxy_this() and deproxy() have to be in places tho

"""
