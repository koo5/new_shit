#invert = monochrome = bg = "cache me"

def cache(settings):
	global invert, monochrome, bg, fg, cursor
	
	invert = settings.find('invert/value')
	monochrome = settings.find('monochrome/value')
		
	s = settings.find('background/items')
	if s:
		bg = s['R'].value, s['G'].value, s['B'].value
	else:
		bg = (0,0,0)
		
	bg = modify(bg)
	
	assert(isinstance(bg, tuple))
	assert(len(bg) == 3)

	cursor = fg = modify((255,255,255))
	


def modify(c, max=255):

	if monochrome and c != (0,0,0):
		c = (255,255,255)

	if invert:
		c = (max - c[0], max - c[1], max - c[2])
		
	return c

