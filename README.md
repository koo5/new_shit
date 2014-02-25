
intro
===
#requires pygame: 
apt-get install python-pygame
#or
pip install --user pygame

talk to us in #lemonparty on freenode (hey, we are already 2 there!)

background noise:  http://goo.gl/jesK0R




license
===
licensing is still a work in progress, to find or develop a suitable
license.  for now, see this experiment: https://github.com/koo5/Free-Man-License
your contributions will be regarded as shared with this future license.
(in legalese: all your contributions are MINE, untill the license is developed
into proper legalese)



bzbzbz
===

"""
node
astnode
dummy
widget
token
tag
"""

menu -> records of user interaction




coupling to pyglet
===
* using pyglets event module
* frontend uses pyglet (duh)
* nodes handle pyglet events
* pyglet makes keypresses into on_text, on_text_motion and on_key_press
* frontend is divisible from backend, just pass around tags and events


more todo ideas
===
* maybe when the language can handle it, move color settings to it,
add some gradient animation
* credits
