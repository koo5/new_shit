what is this
===
a protoprototype of a structural editor and a programming language / user interface, inspired by inform 7, playing with natural language-like projections

<http://imgur.com/a/otY8X#1>




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
talk to us in [](irc://irc.freenode.net/lemonparty)  
old notes:  http://goo.gl/jesK0R ..i kinda stopped working on that one (fuck google docs!)  
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
not decided yet, some standard license or this experiment: <https://github.com/koo5/Free-Man-License> 



