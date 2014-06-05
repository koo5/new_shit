getting started
===
\#requires pygame and fuzzywuzzy:

apt-get install python-pygame
pip install --user fuzzywuzzy #or pip install fuzzywuzzy
it should work with python 2.5, OrderedDict is bundled in

run new_shit.py, or faster.sh if things are slow for you (disables assertions)  
if the latest commit doesnt run, git checkout HEAD^ until you find one that does:)

a menu should appear, the menu reacts to CTRL with up and down   
arrow and inserts an item with space.
Thats kinda all there is to it at the moment!



intro
===
talk to us in irc://irc.freenode.net#lemonparty  
background noise:  http://goo.gl/jesK0R ..i kinda stopped working on that one (fuck google docs!)  
might move everything into lemon nodes :), or a .md on github..  



files:
===
* typed.py (used to be nodes.py): AST classes - "nodes"
* widgets.py textbox, number box, button..
* element.py - both widgets and nodes descend from Element
* project.py: project() "projects" the AST tree onto a grid of text
* new_shit.py: the frontend, handles a window, events, drawing
* colors.py: supposed to keep color settings in one place, doesnt get much love
* tags.py: the result of calling element.render() is a list of tags, these are analogous to html tags
* and menu.py. Plus there are other files around, mostly mess and notes, ignore please.



license
===
licensing is still undecided, usual open source business models dont fit lemon.  
i may choose some standard open source license or continue developing this experiment: <https://github.com/koo5/Free-Man-License>  
crudely something like CC-NC + additional permissions for non-heavy use +  a commercial license  
but for sanity in matters like patents, might try writing something on my own (ha ha)  
clahub isnt ready yet.http://lwn.net/Articles/592503/  
http://www.drdobbs.com/open-source/the-conflict-at-the-heart-of-open-source/240168123  
http://research.microsoft.com/en-us/projects/pex/msr-la.txt  
so, if you want to contribute, you must either give me a CLA or persuade me into a standard license  
this license is just an experiment..side project.. and this version of lemon should be just a bootstrap, so technically it shouldnt matter...



stuff
===
profiling:
python -m cProfile -s cumulative  new_shit.py 



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

