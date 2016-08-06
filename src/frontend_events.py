from keys import *
from lemon_args import args
from collections import namedtuple

class KeypressEvent(object):
	"""a frontend-agnostic keypress event"""
	def __init__(self, all, uni, key, mod):
		"""
		:param all:an array of keys states as provided by SDL_GetKeyState. used for funky sideways cursor moving
		:param uni:unicode value
		:param key:contant from keys.py
		:param mod:-||-
		:param frontend:constant from lemon_platform
		"""
		self.uni = uni
		self.key = key
		self.mod = mod
		self.all = all
		self.type = KEYDOWN

		if args.webos:
			#a hack for my Pre3:
			if self.mod == 0b100000000000000:
				if self.key == K_r:
					self.key = K_UP
				if self.key == K_c:
					self.key = K_DOWN
				if self.key == K_d:
					self.key = K_LEFT
				if self.key == K_g:
					self.key = K_RIGHT

		self.mods = frozenset([x for x in [KMOD_CTRL, KMOD_ALT] if mod & x]) #, KMOD_SHIFT

	def __repr__(self):
		return ("KeypressEvent(key=%s, uni=%s, mod=%s)" %
			(self.key, self.uni, bin(self.mod)))

def mods_to_str(mods):
	r = []
	if KMOD_CTRL in mods:
		r.append("ctrl")
	if KMOD_ALT in mods:
		r.append("alt")
	return r

class MousedownEvent(object):
	def __init__(s, e):
		s.pos = e.pos
		s.button = e.button
		s.type = e.type


ResizeEvent = namedtuple('ResizeEvent', 'size')

