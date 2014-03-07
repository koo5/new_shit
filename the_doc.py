from nodes import Credits, Chapter, Text, URL, List, Syntaxed



def the_doc():
	return List([
	Chapter("profiling","""
	python -m cProfile -s cumulative  new_shit.py
	"""),				
				
	Chapter("coupling to pygame","""
* using <b>pyglets<b> event module (standalone, copied out)
* frontend uses pyglet (duh)
* nodes handle pyglet events
* pyglet makes keypresses into on_text, on_text_motion and on_key_press
* frontend is divisible from backend, just pass around tags and events
"""
	
				
	Chapter("funky wishes", """
	voice recognition (samson?)
	eye tracking
	gradient color changing animation
	"""),
	Chapter("License", 
	Credits()
	
	])
		
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
		
