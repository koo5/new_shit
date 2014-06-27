
from dotdict import dotdict

default_colors = {
	"info item text": (244,244,244),
	"bg": (0,0,0),
	"fg": (255,255,255),
	"cursor": (255,255,200),
	"info item visibility toggle":(100,100,100),
	"menu_rect_selected":(255,255,255),
	"menu_rect":(0,0,255),
    "help":(255,255,0),
    "compiler hint":(100,100,100),
	"text brackets":(200,100,0)
	}

colors = dotdict()

def cache(args):
	global colors, invert, mono
	invert = args.invert
	mono = args.mono
	colors._dict.update(dict([(k, modify(v)) for k,v in default_colors.iteritems()]))

def modify(c, max=255):
	if mono and c != (0,0,0):
		c = (255,255,255)
	if invert:
		c = (max - c[0], max - c[1], max - c[2])
	assert(isinstance(c, tuple))
	return c

def color(c):
	if isinstance(c, str):
		try:
			return colors[c]
		except KeyError:
			raise Exception("i dont know color '%s'" % str(c))
	else:
		return modify(c)