what is this
===
a protoprototype of a structural editor and a programming / shell language / user interface, inspired by inform 7, playing with natural language-like projections

<http://imgur.com/a/otY8X#1>


running it
===
requires pygame and fuzzywuzzy (colors optional)  
pyyaml (python-yaml) for loading saving.
there is a proof-of-concept ncurses frontend  

* apt-get install python-pygame python-pip
* pip install --user fuzzywuzzy colors
#(or without --user)

it should work with python 2.5, OrderedDict is bundled in (maybe not anymore)  

run main_sdl.py, or faster.sh (disables assertions)  
if the latest commit doesnt run, git checkout HEAD^ until you find one that does:)

getting started
===
some info is in intro.txt, some in the builtins module inside lemon,
some context sensitive help is in the sidebars.  
Stop by in the irc channel. I can also take you on a tour in VNC.


resources
===
talk to us in [irc://irc.freenode.net/lemonparty](irc://irc.freenode.net/lemonparty)  
research and discussion: http://goo.gl/1XilSW


help wanted
===
here are some (random) things that i think would help lemon further, sometimes directly, sometimes by making it more
accesible/interesting to other people. Some understanding of lemon is usually
necessary though. I will be more than happy to explain every detail, but be prepared that it takes some time.
some (messy) notes are also towards the end of stuff/the_doc.py, and search for "todo" in the source files..

* support for more human languages.
 would make lemon interesting as a non-english programming tool
 i think this is an easy task. A syntax defined in python code is a list of tags.
 Sometimes you may see them grouped in another list, so there are several alternatives.
 I would wrap each tags list in a dict with additional metadata: "lang" and maybe "verbosity"..  
* help me learn unipycation, yield python or other logic programming functionality.
<http://yieldprolog.sourceforge.net/>
 it will be needed for a lot of features of lemon.
 you dont actually need to know lemon to help me with this

* try adding dbpedia, shell autocompletion or other nodes that have more dynamic menu.
 lemon could find its use with semantic web stuff or attract smart semweb people.
 play with the dynamic menu aspects
 
* help me think thru persistence. node deconstruction/construction. copying,pasting etc

* improve the user interaction with nodes or the context help "system"

* add a generic python function node (from users perspective)

* start building or supporting some complete language, like i7 or lambda calculus or some math symbols or coq or whatever

* add more standard library functions

* employ ipython or any other way to distribute the gui to multiple windows/machines, basically have individual frames talk to the main instance over network

* discuss the license

* help with brython, see hello.html, currently all modules load but nodes.py errors out.
 doesnt have to be very useful (lemon itself isnt yet), just an easy to show thing

* improve the curses frontend, figure out how to detect untranslated sequences or what keys to use

* figure out if projectured <https://github.com/projectured/projectured> or other projects (cedalion, MPS, eastwest..) could be used

* figure out how to have a better font in pygame (for mathy expressions) (see stuff/the_doc.py)

* give me feedback on the builtins module which should for now serve as a de-facto reference to the language

* migrate the google doc to something saner? github wiki? the_doc.py?

* add command line arguments or some other system to select/filter log messages by topic

* revive the_doc.py, the settings module, the toolbar, add support for images or live graphic canvas..

* integrate some test framework, the few tests i have are simply ran on each start

* add more operators, for strings and lists maybe


files
===
* main_sdl.py: the frontend, handles a window, events, drawing. run this one.
* main_curses.py: proof-of-concept console frontend
* lemon.py: frontend-agnostic middlestuff with debug replay functionality
* nodes.py: AST classes
* widgets.py textbox, number box, button..
* element.py - both widgets and nodes descend from Element
* project.py: project() "projects" the AST tree into a grid of text
* tags.py: the results of calling element.render(), text, attribute, child..
* frames.py: the panels: Root, Menu, Info..
* lemon_colors.py: color settings
* lemon_args.py: command line arguments
* stuff/the_doc.py: an attempt to migrate all documentation into lemon



license
===
not decided yet, some standard license or this experiment: <https://github.com/koo5/Free-Man-License> 
For now: By contributing to lemon, you agree to granting me nonexclusive rights to use your contribution (with attribution) within lemon, in any way, including relicensing and reselling. Also, the patent claim protection clauses like in http://www.gnu.org/licenses/agpl-3.0.html apply.;)


