
def cache(settings):
	global invert, monochrome, bg, fg, cursor
	invert = settings['invert'].value
	monochrome = settings['monochrome'].value
	background = modify((0,0,0))
	foreground = modify((255,255,255))
	cursor = modify((200,200,200))


def modify(c, max=255):
	if monochrome and c != (0,0,0):
		c = (255,255,255)
	if invert:
		c = (max - c[0], max - c[1], max - c[2])
	return c
