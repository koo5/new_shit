from __future__ import unicode_literals

from lemon_utils.lemon_six import iteritems, str_and_uni
from lemon_utils.dotdict import dotdict

try:
	#im gonna have to ditch this crappy module
	from colors import *
	assert rgb #assert we didnt import some outdated .pyc
except ImportError as e:
	print(e, "...but nevermind")

default_colors = {
	"info item text": (224,224,224),
	"bg": (0,0,0),
	"highlighted bg":(40,0,0),
	"arrow":(150,150,111),
	"fg": (255,255,255),
	"cursor": (155,255,255),
	"info item visibility toggle":(100,100,100),
	"menu_rect_selected":(255,255,255),
	"menu_rect":(0,0,255),
	"help":(255,255,0),
	"compiler hint":(100,100,100),
	"text brackets":(0,255,0),
	"compiler brackets":(255,255,0),
	"node brackets":(250,150,150),
	"number buttons":(80,80,255),
	"menu item extra info":(0,200,0),
    "eval results":(150,150,150)
	}

colors = dotdict()
#colors._dict = dict(default_colors) #fix dotdict..but not needed..

def cache(args):
	global colors, invert, mono
	invert = args.invert
	mono = args.mono
	colors._dict.update(dict([(k, modify(v)) for k,v in iteritems(default_colors)]))

def modify(c, max=255):
	if mono and c != (0,0,0):#||(0,0,0,0)
		c = (255,255,255)
	if invert:
		c = (max - c[0], max - c[1], max - c[2])
	assert(isinstance(c, tuple))
	return c


def color(c):
	"""return an rgb tuple by name, modified by display filters(mono,invert) and ready for use"""
	if isinstance(c, str_and_uni):
		try:
			return colors[c]
		except KeyError:
			raise Exception("i dont know color '%s'" % str(c))
	else:
		#log(c)
		return modify(c)

#class colors?