what is this
===
a protoprototype of a structural editor and a programming language / user interface, inspired by inform 7, playing with natural language-like projections

<http://imgur.com/a/otY8X#1>
<http://imgur.com/Db7X5ft>


running it
===
\#requires pygame and fuzzywuzzy (colors optional)  
a proof-of-concept ncurses frontend is on the dev branch  

* apt-get install python-pygame python-pip
* pip install --user fuzzywuzzy colors
#(or without --user)

it should work with python 2.5, OrderedDict is bundled in (maybe not anymore)  

run main_sdl.py, or faster.sh (disables assertions)  
if the latest commit doesnt run, git checkout HEAD^ until you find one that does:)

getting started
===
some info is in intro.txt, some in the builtins module inside lemon gui,
some context sensitive things are in the sidebars. Stop by in the irc channel.
I can also take you on a tour in VNC.


resources
===
talk to us in [irc://irc.freenode.net/lemonparty](irc://irc.freenode.net/lemonparty)  
old notes:  http://goo.gl/jesK0R
new notes: stuff/the_doc.py



things to do
===
here are some (random) things that i think would help lemon further, sometimes directly, sometimes by making it more
accesible/interesting to other people. Some understanding of lemon is usually
necessary though. I will be more than happy to explain every detail, but be prepared that it takes some time.
<<<<<<< HEAD
some (messy) notes are also towards the end of stuff/the_doc.py. Also look for #todo in the source files.
=======
some (messy) notes are also towards the end of stuff/the_doc.py, and search for "todo" in the source files..
>>>>>>> dev

* support for more human languages.
 would make lemon interesting as a non-english programming tool
 i think this is an easy task
 
* help me learn unipycation, yield python or other logic programming functionality.
 will be needed for a lot of features of lemon
 you dont actually need to know lemon to help me with this

* try adding dbpedia, shell autocompletion or other nodes that have more dynamic menu.
 lemon could find its use with semantic web stuff or attract smart semweb people.
 play with the dynamic menu aspects
 
* help me think thru persistence. node deconstruction/construction. copying,pasting etc

* improve the user interaction with nodes or the context help "system"

* add a generic python function node (from users perspective)

* start building or supporting some other language, like i7 or lambda calculus or some math symbols or coq or whatever

* add more standard library functions

* ipython or any dumb way to distribute the gui to multiple windows/machines

* discuss the license

* brython, the idea is to give lemon a javascript frontend (everything pygame-specific is in main_sdl.py).
 doesnt have to be very useful (lemon itself isnt yet), just an easy to show thing

* improve the curses frontend.

* figure out how to have a better font in pygame

* give me feedback on the builtins module which should for now serve as a de-facto reference to the language

* migrate the google doc to something saner, like github wiki? or to the_doc.py

* add command line arguments or some other system to select/filter log messages by topic

* revive the_doc.py, the settings module, add support for images or live graphic canvas..

* integrate some test framework

files:
* main_sdl.py: the frontend, handles a window, events, drawing. run this one.
* main_curses.py: proof-of-concept console frontend
* lemon.py: frontend-agnostic middlestuff with debug replay functionality
* nodes.py: AST classes - "nodes"
* widgets.py textbox, number box, button..
* element.py - both widgets and nodes descend from Element
* project.py: project() "projects" the AST tree into a grid of text
* tags.py: the results of calling element.render(), analogous to html tags
* frames.py: the panels: Root, Menu, Info
* lemon_colors.py: color settings
* lemon_args.py: command line arguments
* there are other files around, mostly mess and notes. 
* stuff/the_doc.py: an attempt to migrate all documentation into lemon



license
not decided yet, some standard license or this experiment: <https://github.com/koo5/Free-Man-License> 
For now: By contributing to lemon, you agree to granting me nonexclusive rights to use your contribution (with attribution) within lemon, in any way, including relicensing and reselling. Also, the patent claim protection clauses like in http://www.gnu.org/licenses/agpl-3.0.html apply.

