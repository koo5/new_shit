
_cached_invert_color = False
_cached_posterize_color = False

bg = "cache me"

def cache()
	global _cached_invert_color, _cached_posterize_color
	global bg
	
	_cached_invert_color = find('settings/invert colors/value')
	_cached_posterize_color = False
	
	bg = bg_color()

def modify(c, max=255):

	if _cached_posterize_color:
		c = list(c)
		for i in range(3):
			c[i] = c[i] * 255
		c = tuple(c)

	if _cached_invert_color:
		c = list(c)
		for i in range(3):
			c[i] = max - c[i]
		c = tuple(c)

	return c

def bg_color():
	s = find('settings/background color/items')
	if s == None: return (0,0,100)
	r = s['R'].value
	g = s['G'].value
	b = s['B'].value
	res = modify((r,g,b))
	assert(isinstance(res, tuple))
	assert(len(res) == 3)
	return res

