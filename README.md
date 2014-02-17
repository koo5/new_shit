
intro
===
requires pyglet: pip install --user pyglet

talk to us in #lemonparty on freenode

more info: https://docs.google.com/document/d/1NQCoEghY5rGyEx9tRulQlPz8Do1JPA8O-uoLq3tpTJk/edit



license
===
see LICENSE.md

see also: 
http://tarantsov.com/blog/2012/02/the-third-definition-of-open/
http://wonko.com/post/jsmin-isnt-welcome-on-google-code



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
