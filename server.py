

import lemon_platform

lemon_platform.frontend = lemon_platform.server

import lemon

import collect

lemon.start()


#event -> render ->

def handle(xxX):
	lemon.handle(xxX)

def render_root():
	collect.collect_elem(lemon.root)