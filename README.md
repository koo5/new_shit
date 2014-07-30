what is this
===
a protoprototype of a structural editor and a programming language / user interface, inspired by inform 7, playing with natural language-like projections

<http://imgur.com/a/otY8X#1>




getting started
===
\#requires pygame and fuzzywuzzy:

* apt-get install python-pygame python-pip
* pip install --user fuzzywuzzy #or pip install fuzzywuzzy

it should work with python 2.5, OrderedDict is bundled in

run main.py, or faster.sh if things are slow for you (disables assertions)    
if the latest commit doesnt run, git checkout HEAD^ until you find one that does:)




intro
===
talk to us in [irc://irc.freenode.net/lemonparty](irc://irc.freenode.net/lemonparty)  
old notes:  http://goo.gl/jesK0R
new notes: stuff/the_doc.py



files:
===
* main.py: the frontend, handles a window, events, drawing. run this one.
* nodes.py: AST classes - "nodes"
* widgets.py textbox, number box, button..
* element.py - both widgets and nodes descend from Element
* project.py: project() "projects" the AST tree into a grid of text
* tags.py: the results of calling element.render(), analogous to html tags
* frames.py: the panels: Root, Menu, Info
* colors.py: color settings
* there are other files around, mostly mess and notes. 
* stuff/the_doc.py: an attempt to migrate all documentation into lemon



license
===
not decided yet, some standard license or this experiment: <https://github.com/koo5/Free-Man-License> 
By contributing to lemon, you agree to granting me nonexclusive rights to use your contribution (with attribution) within lemon, in any way, including relicensing and reselling. 
also, the patent claim protection clauses like in http://www.gnu.org/licenses/agpl-3.0.html apply.
some other options: http://www.gnu.org/licenses/gpl-faq.html#AssignCopyright




