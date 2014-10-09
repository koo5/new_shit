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
				Todo("List should have its own menu"),
				Todo("strip leading tabs from text of Notes"),

				Todo("nodeize the doc"),
				Todo("revive old code nodes"),
				Todo("curb hardcoded colors"),
				Todo("multiline text editor"),
				Todo("""modify event.py to not send self to uninterested event handlers
				..try catch
				actually, a lot of that module isnt needed at all
				"""),
				Todo("save/load nodes")
				
			),
					
			Chapter("Introduction", """
				
				syntax of the language is defined by two things: the preferred types
				passed to Placeholders by nodes, and by wat.pl, where a hierarchy is
				defined. In future it would ideally all be in one place.
				
				
				
				"""),
			
			Chapter("Assignment", """
				VariableReference will always reference the declaration ( function argument,
				not an Assignment. so, Assignment will add value to the declaration node,
				menu will not show assignments. we could return to c-style assignment-as-expression
				with a nice wording, like <while <<a>, now becoming <b>,> is <5>...
				
				Assignment to SomethingNew..can lets see how it works as a special case
				
				"""),
			
			Chapter("notes", """
				children as a separate class, avoid __getattr__ magic, allow use of pyDatalog?
				class children
					_dict
					__getattr__
					_types

				"""),
			
			Chapter("notes", """
			
			
				(CNL)
				http://www.irisa.fr/LIS/softwares/squall/
			
				ctrl+enter immediate evaluation

				think the editor can be projectional as it is now,
				will see if it really fits seemless editing. and navigation
				could be primarily structure-based maybe
			
				lemon the language vs lemon the desktop environment..
			
				dont pursue the NodeReference "xpath" stuff, leave it for lemon. although:
				https://code.google.com/p/asq/
				
				connection to jena: http://code.google.com/p/python-graphite/
				
				compilation > interpreter, for this bootstrap
				this thing may be falling apart, but lets see if it can compile itself
				1 interaction
				2 model, syntax 
				how to extend the syntax system,
				requirements:
					input: possible syntaxes of each: True, False, Number
					output:
			"""),
					
			Chapter("type system notes", """
			http://lambda-the-ultimate.org/node/3145
			
			"""),

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
			"""),
			Quote("""It may be simpler to learn a DSL than an equivalent class library, but many people would prefer learning the class library. Class libraries give you something familiar (paradigm + basic language structures) to hold on to, while a DSL is likely completely new. That perception - that a class library is learnable while a new language is a big risk - is a big stumbling block to LanguageOrientedProgramming. """, URL("http://c2.com/cgi/wiki?StumblingBlocksForDomainSpecificLanguages"))
			
					
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
					Language Editing Monster! / Like English, Maybe. Or Not.""")
		
					best syntax for literate-programming? one character starts comment block, different starts code block?
		
		)
		,ReadmeGenerator()
	], False)



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




"""
musings:
version control:
f1: propagate change to master

"lenses":
lense is a custom node
it is declared in some included module
we are in a "console" node - basically a statements list,
ctrl-enter executes current line
the syntax is "songmeanings" <songmeanings search text>
before prolog integration, menu can directly offer the songmeanings node. Asks songmeanings search text node for
autocomplete
SongmeaningsSearchText is a custom node...
in the guts, some sort of asynchronous def songmeanings_autocomplete(text) returning SongmeaningsSearchText nodes with data
or maybe SongmeaningsAuthor, SongmeaningsSong..






dbpedia:use SuRF
<fetch <dbpedia <dbpedia url>>>




status
===
3/6
==
running in pycharm in debugging mode is too slow. optimalization notes:
limiting the amount of lines rendered by render() is kinda useless until
we can limit if from the top, that is, not call render(root) but render(some other element)
and that needs thinking thru but must be doable. Simply dont care if something up there above
the screen changes. Touches upon textual vs nodal navigation. As does deleting children.
draw_menu() is slow, first should be redone to project()
draw_lines is the heavy bit that could be separated out into a C frontend, but that
could get inflexible if more features were wanted. Slightly better is making it a C module
for python..(calling pygame how?)
sanest option might be an alternative python interpreter, just dunno how that would work with pycharm


1/6
==
* added scrolling and sanitized cursor movement a bit
* crude ordering of menu using fuzzywuzzy, based on decl name

31/5
==
* i added some awareness of types to the editor so the slots of nodes can specify a type they accept, as opposed to just a python class of node
* also, added function definition and call nodes (must be tested out yet)
* well, rewrote half of nodes.py, its now typed.py

and pondering what i will do next

* have to introduce the Slot objects yet
* might redo the menu system to actually use the same way of rendering as nodes
* or might work on the contents of the menu..the "palettes" that each node type offers, so inserting nodes actually works again
* (?)or start extending the way Syntaxed specifies syntax now, like, for List, it would be '[', ListItemWithComma*, ListItem?, ']'
* ListItemWithComma, ListItem...implies the concrete syntax nodes would co-exist with the AST nodes..(?)

other todo options:
* triples: predicate definition node, accepts Text or URL as subject and object
* math notations (solve pygame unicode problem)
* add more notes to nodes
* bring shadowedtext back

or start working out what is needed for the more natural way of editing
you dont want to deal with a tree hierarchy all the time, instead,
just a flat list of tokens that keep background information
but i think what i got so far is relevant


PYTHONPATH=~/pygame_cffi pypy new_shit/new_shit.py



Levels of detail
"IP systems also offer several levels of detail, allowing the programmer to "zoom in" or out. In the example above, the programmer could zoom out to get a level that would say something like:
<<print the numbers 1 to 10>>"
en.wikipedia.org/wiki/Intentional_programming




"it" without code figuring out what is meant, draw an arrow instead



why and hows of type systems stuff
http://yager.io/programming/go.html




semantic terminal:
===
>>
>> i would break it down into two parts: the editor-is-terminal part, i
>> think that is also a functionality in emacs, and the "semantic"
>> terminal part:
>>
>> in http://acko.net/blog/on-termkit/ (which seems to have died several
>> years ago right after getting some publicity), commands are strictly
>> made to speak in some JSON encoded format, and plain old ordinary
>> commands run wrapped. You can draw a parallel to a fully structured
>> editor.
sort of post-mortem to termkit from the author:
http://www.reddit.com/r/programming/comments/137kd9/18_months_ago_termkit_a_nextgeneration_terminal/
also: https://news.ycombinator.com/item?id=2559734
but see forks on github.

>>
>> towards the other side of the continuum is http://finalterm.org/ (and that enlightenment thing)
>> which runs bash inside, and only tries to extract information from the
>> text stream. Thats like a semantically aware ide:)
>>
>> i dont know where xiki stands in this, they say "wiki-ish text
>> syntax", i guess it might be a nice middle way.
>>
>>  (another project to mention might be
>> https://github.com/guitarvydas/vsh , but pretty dead too)
>>
>>  Anyway, judging by the google group activity, xiki seems to be a long
>> running project and i hope it gets far, and i will give it a try
>> sometime
>>> http://xiki.org/
>
>heres another: xpipe
>https://vimeo.com/68400623
>
https://github.com/zsh-users/zaw

plan9 terminal too..

http://satyajit.ranjeev.in/2014/07/06/introducing-edi.html




some todo:
===
* (?)or start extending the way Syntaxed specifies syntax now, like, for List, it would be '[', ListItemWithComma*, ListItem?, ']'
* ListItemWithComma, ListItem...implies the concrete syntax nodes would co-exist with the AST nodes..(?)
* triples: predicate definition node, accepts Text or URL as subject and object
* math notations (solve unicode font problem first)
* add notes to nodes




brackets around nodes: doesnt make structure all that clear anyway, try boxing?





		len(self.items) == 1:
			i0 = self.items[0]
			if isinstance(i0, Node):
				r = i0
			#demodemodemo
			elif self.type == b['text']:
				r = Text(i0)
			if self.type == b['number']:
				if Number.match(i0):
					r = Number(i0)






#todo: highlight matching parentheses



we should start thinking about some scenegraphotoolkitoframeworkthing
i want to define all my keypress and mouse responses declaratively
oh and i want actions like in photoshop. 


stuff that lemon wants to use:
pypy:
pypy compiles your rpython-annotated code into a JITting interpreter. how cool is that?
but it makes interacting with ctypes (?) based c extensions slow.
http://morepypy.blogspot.cz/2014/03/pygamecffi-pygame-on-pypy.html
pygame_cffi wasnt finished, missed drawing something lemon needed, last time i checked

https://bitbucket.org/pypy/compatibility/wiki/Home#!gamemultimedia-libraries

kivy:
graphics framework
compatible with pypy: doesnt look like happening. it is written in Cython, a sort of
contender to pypy
but, if we split frontend and backend..hmm..
<kovak> there is nothing to stop you from using Kivy's providers directly<kovak> one of which is SDL<kovak> there has even been a recent discussion about a more low level text api


simple options:
tkinter:
try how tkinter works with pygame (would events go thru pygame or tkinter? 
its probably a hour of work to update the events handling, several more to 
rewrite new_shit.py ...
maybe i dont want to fight with a standard toolkit about focus.
https://mail.python.org/pipermail/tutor/2012-September/091417.html

pygame gui libs:
ocempgui isnt packaged, does it work from source tree?
pgu




libavg: cool, but too much of a moving target?





so, what do we want:
access to SDL_ttf or other low level text drawing, preferably with both software and opengl backends

at some point make lemon distributed, with ipython or some object proxying lib.
each window or computer can display different frames. i never did this kind of thing, 
so i dont know performance-wise where it will be best to make the "cuts"


at some (distant) point, change to rpython, start using pypy

we want graphics, opengl, but compatibility with non-accelerated machines too
(an option to disable wild graphics and still run)

what widgets do we want: for a start, panels to embed lemon frames in. with the line
between them that you can drag to resize them. then maybe tabs. maybe file open dialog
some of these things would be fun to do in lemon widgets but why.
also, we may find that using standard widgets is useful, maybe popping up around lemon
code or something, maybe that text editor.
So yeah there would be both lemon text-o-widgets and some different widgets. but who cares.


oh, and im eyeing pyglet again. 


if somebody will want to do a JS version, there are python-to-js compiler/interpreter projects. what would be the implications of their use for $above/of $above for their use?





hard stuff to get done: 
>Compiler.on_keypress: maybe some abstraction like this_is_left_bracket_of_item_1, this_is_...
understand yield python or try pyDatalog again or .. /me cries
that damned license





<Hmm>





http://programmers.stackexchange.com/questions/208677/how-to-handle-divide-by-zero-in-a-language-that-doesnt-support-exceptions
"If you divie floating point numbers, Nan or Inf would be nice (have a look at IEEE 754 to understand why). If you divide integers, you may stop the program, divide by 0 should never be allowed"
 i like "(to n)"<stickittothemain> yeah, i didnt want to copy python exactly<sirdancealot> should go steal that right away<stickittothemain> i'll make a better example<sirdancealot> actually that raises some curious questions about lemon. Something tells me that rather than implementing it as a new function, it could be an alternative syntax for the "numbers from X to Y" i have<sirdancealot> an alternative syntax where the first argument is hidden<sirdancealot> which would make it empty i guess<sirdancealot> which would result in Bananas<sirdancealot> (compilation error, ok)<sirdancealot> i think gremble_ wouldnt agree with calling it Bananas<sirdancealot> so, it raises the question if we want such compilation errors to just produce a vlue and continue executon
 serious languag will not compiler/have exceptions etc ofc, but its still interesting experiment
[for live programming. is it?]


http://www.lispme.de/lispme/angif.htm




todo / direction:
===
start actually doing some parsing:
	im currently playing with unipycation
replace pygame and/or employ a widget framework, at least to manage the panels on the screen

editing, not just insert / delete node
tagged text - nodes transformation:
	this doesnt actually depend on parsing that much, can start right away(after figuring out how)

save/load: at least a stupid serialization / deserialization

ncurses interface




* all around finish things





#⇾node⇽...would be nice...how to ensure having a good unicode font available? bundle?
http://stackoverflow.com/questions/586503/complete-monospaced-unicode-font
gpl: we could offer to wget it - ..
or just have a script in the project dir for now
wonder why the default doesnt support much unicode? dunno
http://www.pygame.org/docs/ref/font.html#pygame.font.SysFont
yeah i saw that
sorry but i should go back to studying today ok
sorry to interrupt, but have you heard of restructuredtext?yes
its the same shit as markdown, tried it ok
github offers several more formats for wikis, but they all seemed to suck
i'll make my own i was thinking about it too
all i want is headings and clickable links
easy to generate a markdown from it then
markdown and html? maybe..markdown and rst and maybe others is what github
then renders
sorry, im not making much sense today thats fine
another option would be to use markdown mode in emacs, i tried some 
web markdown editor yesterday, it was like, semi wysiwyg, its enough
if the emacs mode is like that, that would be cool
except the learning emacs part

==section== hows that?fine
im thinking tho, the === sections as markdown does this are fine,
it hardly ever conflicts with anything..except the forgotten merge conflicts

(http://example.tld/x/y/z): click me!
hows that?hmm, as long as it makes sure its a link inside the parentheses
but then you dont need the parentheses
parens make it easier to parseok

hmm
trying to work out newlines in the simplest way
cant s/\n/\n\n/
so, what are you doing, generating markdown?
yes. it expects two spaces at the end of line. i would just add two spaces everywhere
really  that  sounds  like  it  would  work  fine.i mean at line ends ok
would be damn nice to actually detect those merge conflict lines..and just throw a warning
or something, just dont let markdown make them into those huge headinh
what are the conflicts?





possible todo path towards an useful language:
===
save/load:
	identification

copy/paste	

python eval:
	class variable for environment	
	phase 2: PythonEvalText, menu, __dict__

structs



priorities: 
persistence -> settings
PythonFunction
unipycation

http://heritagerobotics.wordpress.com/2012/11/20/compiling-pygame-for-python-3-2-in-xubuntu/



stub event.py:
+
+	def register_event_types(self, types):
+		pass
+	def push_handlers(self, *args, **kwargs):
+		pass
+	def dispatch_event(self, event_type, *args):
+		pass
+

https://techbase.kde.org/Development/Tutorials/Shell_Scripting_with_KDE_Dialogs
http://linuxgazette.net/101/sunil.html





adaptive/high level:
http://www.whenappsfly.com/how-it-works/
http://en.wikipedia.org/wiki/Metaobject_protocol
http://norvig.com/adapaper-pcai.html



lesh:
start with a Lesh node - thats the command line
later: history or more fancy (xiki style) stuff or whatever
one child of type LeshCommand
->creates parser
hack parser to offer LeshSnippet
based on current word, not whole text
or some boundary (|), this is also where you need to split the text into tokens
hack(subclass?) snippet menu item to insert plain text

menu movement with pgup pgdown, i dunno how to best handle the curses sequences yet



dialogs from development
==
pygame font
===
pygame loads/uses some default font that doesnt support some unicode glyphs
what font would you like? maybe ubuntu? i have no idea hmm
..apparently ubuntu has a lot of unicode glyphs . i just know that we cant bundle a cool free unicode font because of the license
but lemon could try to download it, in the installer? in the installer it doesnt have
where does ubuntu keep it's fonts? i think i know where osx does
dunon, theres gonna be some environment var and stuff
deja vu sans? it's on by default on the linux distros ive seen, windows, and osx, and has really good unicode support
i dunno. i guess this task is bogus. It might be more important if we wanted to render math symbols for example
i just thought it would be nice to have some unicode glyphs for buttons but the font loaded by pygame by default didnt have them
if you can figure out how to make pygame look harder or something..i dunno
well, you cant make pygame look harder, 
cant you just get the os, check in it's 'fonts' folder, check for the font, if not found then use the default without cool unicodes?
yeah, something like that. Maybe just try loading some better one and pygame will fall back to default if not found
=======


the curse of automatization


http://stromberg.dnsalias.org/~strombrg/pybrowser/python-browser.html




# region Unknown
"""
class Unknown(WidgetedValue):
	will probably serve as the text bits within a Parser.
	fow now tho, it should at least be the result of explosion,

	explosion should replace a node with an Unknown for each TextTag and with its
	child nodes. its a way to try to add more text-like freedom to the structured editor.

	currently a copypasta of Text.
	def __init__(self, value=""):
		super(Unknown, self).__init__()
		self.widget = widgets.Text(self, value)
		self.brackets_color = "text brackets"
		self.brackets = ('?','?')

	def render(self):
		return self.widget.render()

	def on_keypress(self, e):
		return self.widget.on_keypress(e)

	def _eval(self):
		return Text(self.pyval)

	def long__repr__(s):
		return object.__repr__(s) + "('"+s.pyval+"')"

	@staticmethod
	def match(text):
		return 0
"""
# endregion



fonts:
http://forum.lazarus.freepascal.org/index.php?topic=20193.0





"""
here i was messing with an intermediate step between serialized data and nodes
that would allow interactive resolving
class Unresolved(Node):
	def __init__(s, data, root = None):
		if isinstance(data, dict):
			s.data = data
		elif isinstance(data, Node):
			s.data = data.unresolvize()
#		elif
	def serialize(s):
		r = {}
		log("serializing Unresolved with data:", s.data)
		for k,v in iteritems(s.data):
			if isinstance(v, str_and_uni):
				r[k] = v
			elif k == "decl":
				r[k] = v.name
				log(v.name)
			else:
				r[k] = str(v)
		return r


def serialized2unresolved(d, r):
	new = Unresolved({})
	if 'text' in d:
		new.data['text'] = d['text']
	if 'target' in d:
		new.data['target'] = serialized2unresolved(d['target'], r)

	#if 'children' in d:
	#	new.data['children'] = {[(k, deserialize(v)) for k, v in d['children']]}


	return new


@topic ("serialization")
def test_serialization(r):

	#---from serialized to unresolved and back
	log("1:")
	ser = {
	'decl' : 'number',
	'text' : '4'
	}
	unr = Unresolved(i, r)
	log(out)
	ser = out.serialize()
	assert ser == i, (ser, i)

#NodeFinder?
"""





http://pygame.org/wiki/CompileUbuntu?parent=Compilation







intro
	why lemon
		textual projection:
			cool natlanging, editing
				alternatives;
					citrus
					cedalion
					mps
			