"""this file works as a rpc interface, so instead of looking for the perfect rpc library,
i will just rewrite it into a little less oop-y style, so the clients dont have to be able
to access complex objects as atributes of this file, but just call various functions"""

from __future__ import unicode_literals

import graph

import lemon_platform as platform
from lemon_colors import color, colors

import nodes
from element import Element
from menu_items import InfoItem
from tags import TextTag, ElementTag, MemberTag, ColorTag, EndTag, AttTag
import widgets
from lemon_utils.lemon_logger import log, topic

from lemon_utils.lemon_six import iteritems, str_and_uni
from lemon_args import args
from lemon_utils.utils import evil

from pizco import Signal

class ServerFrame(object):

	def __init__(s):
		pass


class Editor(ServerFrame):
	def __init__(self):
		super(Editor, self).__init__()

		self.root = nodes.make_root()
		self.root.fix_parents()

		self.root.ast_changed.connect(self.on_root_changed)
		self.root.changed.connect(self.on_root_changed)
		self.on_root_change = Signal()
	#can we chain these somehow?
	def on_root_changed(s):
		s.on_root_change.emit()

	def tags(s):
		return s.root.tags()

	@property
	def element_under_cursor(s):
		return atts[att_node]

editor = Editor()

def editor_notify_cursor_on_atts(atts):
	assert type(atts) == dict
	editor.atts = atts

def editor_run_active_program():
	editor.root['some program'].run()

def editor_run_line():
	editor.atts[node_att].module.run_line(root.atts[node_att])

def editor_clear():
	editor.root['some program'].clear()

def	editor_dump_root_to_file():
	pass

def editor_get_delayed_cursor_move():
	return editor.root.delayed_cursor_move



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
	info = []
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



class Log(ServerFrame):
	def __init__(s):
		super(Log, s).__init__()
		s.items = []

	def add(s, msg):
		#timestamp, topics, text = msg
		#if type(text) != unicode:
		s.items.append(str(msg))
		print(str(msg))



def collect_tags(proxied_serverframe):
	return deproxy(proxied_serverframe).collect_tags()

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










"""
general ways that rpcing complicates things;

have to do more effort at proper mvc-y eventing, but this would in some form be
necessary for best performance anyway (keeping track of dirtiness at various levels

proxying elements: wont be a performance hit, if it will, it can be easily stubbed
proxy_this() and deproxy() have to be in places tho


"""
