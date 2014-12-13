"""rpcing client. alternatively, it could just thread"""

import operator
import types


from lemon_utils.dotdict import Dotdict
from lemon_utils.lemon_six import unicode, itervalues

from .marpa_misc import *


class MarpaClient(object):
	def __init__(s, debug=True):
		s.debug = debug
		s.named_syms = Dotdict()
		s.syms = {}
		s.known_chars = {}
		s.rules = {}
		s.named_symbol('known_char')

	def named_symbol(s,name):
		"""create a symbol and save it in syms with the name as key"""
		if s.debug:
			if name in s.named_syms._dict:
				raise Exception("%s already in named_syms"%name)
		r = s.named_syms[name] = s.symbol(name)
		return r

	def symbol(s,debug_name):
		if s.debug:
			pyid = len(s.syms)
			s.syms[pyid] = (debug_name)
		else:
			raise Exception("#todo, just use a counter")
		return pyid

	def symbol2name(s,symid):
		assert s.debug
		return s.syms[symid]

	def rule2name(s,r):
		assert s.debug
		return s.rules[r]

	def rule(s,debug_name, lhs,rhs,action=ident):
		if type(rhs) != list:
			rhs = [rhs]

		if __debug__:
			assert type(lhs) == symbol_int
			for i in rhs:
				assert type(i) == symbol_int
			assert type(debug_name) == unicode
			assert type(action) == types.FunctionType

		s.rules.append((False, debug_name, lhs, rhs, action))

	def sequence(s,debug_name, lhs, rhs, action=ident, separator=-1, min=1, proper=False):
		assert type(lhs) == symbol_int
		assert type(rhs) == symbol_int
		assert type(debug_name) == unicode
		s.rules.append((True, debug_name, lhs, rhs, action, separator, min, proper))

	def known_char(s, char):
		"""create a symbol for a single char"""
		if char not in s.known_chars:
			r = s.known_chars[char] = s.symbol(char)
			s.rule(char+"_is_known_char", s.syms.known_char, r)
		return r

	def known_string(s, string):
		"""create a symbol for a string"""
		rhs = [s.known_char(i) for i in string]
		lhs = s.symbol(string)
		s.rule(string+'_is_known_string', lhs, rhs, join)
		return lhs

	def set_start_symbol(s,start):
		s._start_symbol = start

	def raw2tokens(s,raw):
		"""return a list with known chars substituted with their corresponding symbol ids"""
		tokens = []
		for i, char in enumerate(raw):
			if char in s.known_chars:
				symid=s.known_chars[char]
			else:
				symid=s.syms.nonspecial_char
			tokens.append(symid)
		return tokens

	@staticmethod
	def sorted_by_values(dotdict):
		return sorted(dotdict._dict.items(),key=operator.itemgetter(1))

	@property
	def syms_sorted_by_values(s):
		return s.sorted_by_values(s.syms)

	def check_accessibility(s):
		for i in s.syms._dict.items():
			if not s.g.symbol_is_accessible(i[1]):
				raise Exception("inaccessible: %s (%s)"%i)

