
def cache(args):
	global invert, mono, bg, fg, cursor
	invert = args.invert
	mono = args.mono
	bg = modify((0,0,0))
	fg = modify((255,255,255))
	cursor = modify((200,200,200))


def modify(c, max=255):
	if mono and c != (0,0,0):
		c = (255,255,255)
	if invert:
		c = (max - c[0], max - c[1], max - c[2])
	return c
