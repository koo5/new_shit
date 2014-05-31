getting started
===
#requires pygame: 
apt-get install python-pygame

run new_shit.py, or faster.sh if things are slow for you (disables assertions)
if the latest commit doesnt run, git checkout HEAD^ until you find one that does

a menu should appear, the menu reacts to CTRL with up and down 
arrow and RETURN. that kinda shows everything there is to the program at the moment!



intro
===
talk to us in irc://irc.freenode.net#lemonparty
background noise:  http://goo.gl/jesK0R ..i kinda stopped working on that one (fuck google docs!)
might move everything into lemon nodes :), or a .md on github..



license
===
licensing is still undecided, usual open source business models dont fit lemon.
i may choose some standard open source license or
continue developing this experiment: <https://github.com/koo5/Free-Man-License>
crudely something like CC-NC + additional permissions for non-heavy use +  a commercial license
but for sanity in matters like patents, might try writing something on my own (ha ha)
clahub isnt ready yet.http://lwn.net/Articles/592503/
http://www.drdobbs.com/open-source/the-conflict-at-the-heart-of-open-source/240168123
http://research.microsoft.com/en-us/projects/pex/msr-la.txt
so, if you want to contribute, you must either give me a CLA or persuade me into a standard license
this license is just an experiment..side project.. and this version of lemon should be just a bootstrap,
so technically it shouldnt matter...



stuff
===
profiling:
python -m cProfile -s cumulative  new_shit.py 



status
===
31/5
i added some awareness of types to the editor
so the slots of nodes can specify a type they accept, as opposed to just a python class of node
actually, will have to introduce the Slot objects yet
also, added function definition and call nodes
well, rewrote half of nodes.py, its now typed.py
and pondering what i will do next
might redo the menu system to actually use the same way of rendering as nodes...then add scrolling
coz nothing scrolls yet
or might work on the contents of the menu..the "palettes" that each node type offers, so inserting nodes actually works again
or start working out what is needed for the more natural way of editing
like, i see now the sweet spot could be some quantum-mechanic-like superposition
you dont want to deal with a tree hierarchy all the time, instead, just a flat list of tokens that keep background information
but i think what i got so far is relevant
(?)or start extending the way Syntaxed specifies syntax now, like, for List, it would be '[', ListItemWithComma*, ListItem?, ']'
ListItemWithComma, ListItem...implies the concrete syntax nodes would co-exist with the AST nodes..(?)
other todo options: triples, math notations
