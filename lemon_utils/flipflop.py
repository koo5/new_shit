__author__ = 'kook'

from pizco.util import Signal

class FlipFlop(Signal):
	def set(s):
		if not s._is_set:
			s.emit()
		s._is_set = True

	def reset(s):
		s._is_set = False
