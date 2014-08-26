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



files
===
* main.py: the frontend, handles a window, events, drawing. run this one.
* lemon.py: frontend agnostic stuff
* nodes.py: AST classes - "nodes"
* widgets.py textbox, number box, button..
* element.py - both widgets and nodes descend from Element
* project.py: project() "projects" the AST tree into a grid of text
* tags.py: the results of calling element.render(), analogous to html tags
* frames.py: the panels: Root, Menu, Info
* lemon_colors.py: color settings
* there are other files around, mostly mess and notes. 
* stuff/the_doc.py: an attempt to migrate all documentation into lemon



license
===
not decided yet, some standard license or this experiment: <https://github.com/koo5/Free-Man-License> 
For now: By contributing to lemon, you agree to granting me nonexclusive rights to use your contribution (with attribution) within lemon, in any way, including relicensing and reselling. Also, the patent claim protection clauses like in http://www.gnu.org/licenses/agpl-3.0.html apply.

