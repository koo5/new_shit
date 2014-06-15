
default_colors = {
	"info item text": (244,244,244),
	"bg": (0,0,0),
	"fg": (255,255,255),
	"cursor": (255,255,200),
	"info_item_visibility_toggle":(100,100,100)
	}

colors = 666

def cache(args):
	global colors, invert, mono
	invert = args.invert
	mono = args.mono
	colors = dict([(k, modify(v)) for k,v in default_colors.iteritems()])

def modify(c, max=255):
	if mono and c != (0,0,0):
		c = (255,255,255)
	if invert:
		c = (max - c[0], max - c[1], max - c[2])
	return c
