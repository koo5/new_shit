from nodes import Credits, Chapter, Text, URL, List, Syntaxed, Node



def the_doc():
	return List([
		Chapter("development", List([
			Chapter("todo",	List([
				Todo("strip leading tabs from text of Notes"),
				Todo("""bool, syntaxed, how? enum,
				True and False separate atoms with syntaxes?
				"""),
				Todo("nodeize the doc"),
				Todo("revive old code nodes"),
				Todo("curb hardcoded colors"),
				Todo("multiline text editor"),
				Todo("save/load nodes")
			])),
					
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
			
					
		])),

		Chapter("introduction", List([
			Chapter("wtf is this? / Что это?",
			"""what you see in the editor window is a tree of AST nodes and other, helper,
			elements like gui widgets. They are rendered onto a text grid, and you can move
			around with a cursor..."""),
			Chapter("accesibility", """done: color inversion, background color and font size. "posterization" (full black or white) is underway. . . .?
			hardcoded colors are currently getting out of hand
			"""),
			Chapter("speed", """try python -O ( ./faster.sh ), disables assertions, makes things usable"""),
			Chapter("license", """licensing is still a work in progress, to find or develop a suitable license.  for now, see this experiment: """,URL(https://github.com/koo5/Free-Man-License),"""
			your contributions will be regarded as shared with this future license.
			(in legalese: all your contributions are MINE, untill the license is developed
			into proper legalese)
			""")
		])),

		Credits(),

		Chapter("compost heap", List([
			
			
		]))
	])



def readme(doc):
	return List([
		Chapter("getting started", """
			requires python version 2 and pygame: 
			apt-get install python python-pygame
			or
			pip install --user pygame

			talk to us in #lemonparty on freenode (hey, we are already 2 there!)
			"""),	
		NodeReference("name=introduction/0"),
		NodeReference("name=introduction/name=license")
	])


class ReadmeGenerator(Syntaxed):

	def __init__(self, doc):
		super(Chapter, self).__init__()
		self.body = readme(
		self.text = FancyText(text)
		self.syntaxes = [[w('title'), nl(), w('text')]]

class Chapter(Syntaxed):

	def __init__(self, title, text):
		super(Chapter, self).__init__()
		self.title = title
		self.text = FancyText(text)
		self.syntaxes = [[w('title'), nl(), w('text')]]

class FancyText(Node):

	def __init__(self, value):
		super(Chapter, self).__init__()
		if isinstance(value, str):
			value = [str]
		for i,x in enumerate(value):
			if isinstance(x, str):
				value[i] = Text(x)
		self.value = value
		
class NodeReference(Syntaxed):
	
	def __init__(self, path):
		assert(isinstance(path, str))
		self.path = widgets.Text(path)
		self.syntaxes = [[t("node path:"), w('path'), nl(), w('node')]]
		self.refresh_button = widgets.Button("not found, refresh.")
		self.path.push_handlers(on_change = self.refresh)
		self.refresh_button.push_handlers(on_click = self.refresh)
		self.refresh('__init__')
		
	def refresh(self, widget):
		self.node = find(self.path.text)
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
						 [t("pyglet authors - lemon uses event.py copied from pyglet")]]
						 [t("...")]]
