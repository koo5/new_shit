what is this
===
a protoprototype of a structure editor and of a programming language / user interface vision inspired by inform 7





getting started
===
\#requires pygame and fuzzywuzzy:

* apt-get install python-pygame
* pip install --user fuzzywuzzy #or pip install fuzzywuzzy

it should work with python 2.5, OrderedDict is bundled in

run new_shit.py, or faster.sh if things are slow for you (disables assertions)    
if the latest commit doesnt run, git checkout HEAD^ until you find one that does:)




intro
===
talk to us in irc://irc.freenode.net#lemonparty  
background noise:  http://goo.gl/jesK0R ..i kinda stopped working on that one (fuck google docs!)  
might move everything into lemon nodes :), or a .md on github..  



files:
===
* new_shit.py: the frontend, handles a window, events, drawing. run this one.
* typed.py (nodes.py is outphased): AST classes - "nodes"
* widgets.py textbox, number box, button..
* element.py - both widgets and nodes descend from Element
* project.py: project() "projects" the AST tree onto a grid of text
* tags.py: the result of calling element.render() is a list of tags, these are analogous to html tags
* menu.py
* colors.py: supposed to keep color settings in one place, doesnt get much love
* there are other files around, mostly mess and notes. 
* the_doc.py: an attempt to migrate all documentation into lemon



license
===
i may choose some standard license or continue developing this experiment: <https://github.com/koo5/Free-Man-License>  
this license is just an experiment..side project.. and this version of lemon should be just a bootstrap, so technically it shouldnt matter...
so, if you want to contribute, you must either give me a CLA or persuade me into a standard license  




stuff
===
profiling:
python -m cProfile -s cumulative  new_shit.py 




some todo:
===
* draw_menu() is slow, first should be redone to project()
* have to introduce the Slot objects yet
* (?)or start extending the way Syntaxed specifies syntax now, like, for List, it would be '[', ListItemWithComma*, ListItem?, ']'
* ListItemWithComma, ListItem...implies the concrete syntax nodes would co-exist with the AST nodes..(?)
* triples: predicate definition node, accepts Text or URL as subject and object
* math notations (solve pygame unicode problem first)
* add more notes to nodes
* bring shadowedtext back
* move to Unipycation
* type system
