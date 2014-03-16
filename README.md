getting started
===
#requires pygame, swi-prolog and pyswip: 
apt-get install python-pygame swi-prolog
#and
pip install --user pyswip

run new_shit.py, or faster.sh if things are slow for you (disables assertions)
if the latest commit doesnt run, git checkout HEAD^ until you find one that does

once the program starts, you can press right arrow to get over the [statement] placeholder, 
a menu should appear, you can type something in. the menu reacts to CTRL with up and down 
arrow and RETURN. that kinda shows everything there is to the program at the moment!



intro
===
talk to us in #lemonparty on freenode (hey, we are already 2 there!)
background noise:  http://goo.gl/jesK0R




license
===
licensing is still a work in progress, to find or develop a suitable
license.  for now, see this experiment: <https://github.com/koo5/Free-Man-License>
your contributions will be regarded as shared with this future license.
(in legalese: all your contributions are MINE, untill the license is developed
into proper legalese)




stuff
===
profiling:
python -m cProfile -s cumulative  new_shit.py 
