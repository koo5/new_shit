# -*- coding: utf-8 -*-

import project
import widgets
from nodes import Text, List, Syntaxed, Node, Todo, Note, Collapsible
from tags import ElementTag, NewlineTag as nl, WidgetTag as w, TextTag as t, ChildTag as ch
from logger import ping

def the_doc():
	return List([
		Chapter("development", 
			Chapter("todo",	
				Todo("strip leading tabs from text of Notes"),
				Todo("""bool, syntaxed, how? enum,
				True and False separate atoms with syntaxes?
				"""),
				Todo("nodeize the doc"),
				Todo("revive old code nodes"),
				Todo("curb hardcoded colors"),
				Todo("multiline text editor"),
				Todo("modify event.py to not send self to uninterested event handlers"),
				Todo("save/load nodes")
			),
					
			Chapter("funky wishes", """
			voice recognition (samson?)
			eye tracking
			gradient color changing animation
			
			systemic changes to consider:
				projectured needs to be tried out and evaluated for a possible use as the base of lemon.
				maybe also emacs
			"""),
			
			Chapter("profiling", """
			python -m cProfile -s cumulative  new_shit.py
			"""),				
			Chapter("coupling to pygame", """
			* using pyglets event module (standalone, copied out)
			* frontend uses pygame
			* nodes handle pygame events (keyboard and mouse)
			* frontend could be divided from backend, just passing lines and events back and forth
			""")
			
					
		),

		Chapter("introduction", 
			Chapter("wtf is this? / Что это?",
			"""what you see in the editor window is a tree of AST nodes and other, helper,
			elements like gui widgets. They are rendered onto a text grid, and you can move
			around with a cursor...
			text is white, red <s and >s show starts and ends of elements
			you can move the cursor to a spot with green and yellow <>s,
			thats a Placeholder.
			the thing on the right side is a menu, and shows what node you are on,
			and what items you can insert in the place.
			
			"""),
			Chapter("accesibility", """done: color inversion, background color and font size. "posterization" (full black or white) is underway. . . .?
			hardcoded colors are currently getting out of hand
			"""),
			Chapter("speed", """try python -O ( ./faster.sh ), disables assertions, makes things usable"""),
			Chapter("license", """licensing is still a work in progress, to find or develop a suitable license.  for now, see this experiment: """,URL("https://github.com/koo5/Free-Man-License"),"""
			your contributions will be regarded as shared with this future license.
			(in legalese: all your contributions are MINE, untill the license is developed
			into proper legalese)
			""")
		),

		Credits(),

		Chapter("compost heap", 
			Note("""unasked questions:
					what does lemon stand for?
					Language Editing Monster!""")
		
		
		
		)
		,ReadmeGenerator()
	])



class ReadmeGenerator(Syntaxed):

	def __init__(self):
		super(ReadmeGenerator, self).__init__()
		self.setch('body', List([
		Chapter("getting started", """
			requires python version 2 and pygame: 
			apt-get install python python-pygame
			or
			pip install --user pygame

			talk to us in #lemonparty on freenode (hey, we are already 2 there!)
			
			if latest version doesnt compile, try older: git checkout HEAD^
			"""),	
		NodeReference("docs/title=introduction/0"),
		NodeReference("docs/title=introduction/name=license")
		]))

		self.button = widgets.Button(self, "generate README.md")
		self.syntaxes = [[w('button'), nl(), ch('body')]]
		self.button.push_handlers(on_click = self.generate)
		
	def generate(self, widget):
		ping()
		f = open("README.md", "w")
		project._width = 80
		lines = project.project(self)
		for line in lines:
			for char in line:
				f.write(char[0])
			f.write("\n")
		f.close()
		

class Chapter(Collapsible):

	def __init__(self, title, *body):
		super(Chapter, self).__init__(False)
		self.title = widgets.Text(self, title)
		if isinstance(body[0], str):
			body = FancyText(list(body))
		else:
			body = List(list(body))
		self.setch('body', body)
		
	def render_items(self):
		if self.expanded:
			return [w('title'), nl(), ch('body')]
		else:
			return [w('title')]



class URL(str):
	
	pass
	
	
	
class FancyText(Node):

	def __init__(self, value):
		super(FancyText, self).__init__()
		#for i,x in enumerate(value):
		#	if isinstance(x, str):
		#		r = ""
		#		for line in x.split("\n"):
		#			r += line.strip()
		#		value[i] = Text(r)
		self.value = [x.strip() for x in value]
	def render(self):
		#return [ElementTag(x) for x in self.value]
		return [t(x) for x in self.value]
		
		
		
class NodeReference(Syntaxed):
	
	def __init__(self, path):
		super(NodeReference, self).__init__()
		assert(isinstance(path, str))
		self.path = widgets.Text(self, path)
		self.syntaxes = [[t("node path:"), w('path'), nl(), w('node')]]
		self.refresh_button = widgets.Button(self, "not found, refresh.")
		self.path.push_handlers(on_edit = self.refresh)
		self.refresh_button.push_handlers(on_click = self.refresh)
		self.node = self.refresh_button

	def refresh(self, widget):
		self.node = self.root.find(self.path.text)
		if self.node == None:
			self.node = self.refresh_button



class Credits(Syntaxed):

	def __init__(self):
		super(Credits, self).__init__()
		self.syntaxes = [[t("this project would suck much more without:")],
						 [t("theplic - made me write the doc")],
						 [t("gremble - actually understood the whole idea")],
 						 [t("AnkhMorporkian - his coding frenzy brought about the projection system")],
 						 [t("rszeno - had endless patience")],
						 [t("pyglet authors - lemon uses event.py copied from pyglet")],
						 [t("...")]]
