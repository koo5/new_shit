from nodes import Credits, Chapter, Text, URL, List, Syntaxed



def the_doc():
	return List([


			"notes", List([
				Todo("strip leading tabs from text of Notes"),
				Todo("""bool, syntaxed, how?
				True and False separate atoms with syntaxes?
				
				"""),
				Todo("nodeize the doc"),
				Todo("revive old code nodes"),
				Todo("curb hardcoded colors"),
				Todo("multiline text editor"),
				Todo("save/load nodes")
				], False)


	Chapter("accesibility","""done: color inversion, background color and font size. "posterization" (full black or white) is underway. . . .?
	hardcoded colors are currently getting out of hand
	"""),
	Chapter("speed", """try python -O ( ./faster.sh ), disables assertions, makes things usable"""),
	Chapter("profiling","""
	python -m cProfile -s cumulative  new_shit.py
	"""),				
	Chapter("coupling to pygame","""
* using pyglets event module (standalone, copied out)
* frontend uses pygame
* nodes handle pygame events (keyboard and mouse)
* frontend could be divided from backend, just passing lines and events back and forth
""")
	Chapter("funky wishes", """
	voice recognition (samson?)
	eye tracking
	gradient color changing animation
	"""),
	Chapter("license", """licensing is still a work in progress, to find or develop a suitable
license.  for now, see this experiment: """,URL(https://github.com/koo5/Free-Man-License),"""
your contributions will be regarded as shared with this future license.
(in legalese: all your contributions are MINE, untill the license is developed
into proper legalese)
"""),
	Credits()
	
	])



def readme(doc):
	return List([


intro
===
#requires pygame: 
apt-get install python-pygame
#or
pip install --user pygame

talk to us in #lemonparty on freenode (hey, we are already 2 there!)

background noise:  http://goo.gl/jesK0R


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
		
