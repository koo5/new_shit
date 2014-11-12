import operator
from marpa import *
from dotdict import *
from lemon_six import str_and_uni

#some parser action callbacks

def ident(x):
	assert len(x) == 1
	return x[0]

def join(args):
	return ''.join(args)


class HigherMarpa(object):
	def __init__(s):
		"""create a new grammar object and stuff"""
		s.rules = dotdict()
		s.syms = dotdict()
		s.g = Grammar()
		s.known_chars = {}
		s.actions = {} # per-rule valuator callbacks (functions that the parser steps loop calls to actually create basic values or Nodes from lists of values or child nodes

	def symbol(s,name):
		"""create a symbol and save it in syms"""
		r = s.g.symbol_new()
		if name in s.syms._dict:
			raise Exception("%s already in syms"%name)
		s.syms[name] = r
		return r

	def symbol2name(s,symid):
		for k,v in s.syms._dict.items():
			if v == symid:
				return k
		assert False

	def rule2name(s,r):
		for k,v in s.rules._dict.items():
			if v == r:
				return k
		assert False

	def rule(s,name, lhs,rhs,action=ident):
		assert type(name) in str_and_uni
		assert name not in s.rules._dict
		assert type(lhs) == symbol_int

		if type(rhs) != list:
			assert type(rhs) == symbol_int
			rhs = [rhs]
		r = s.rules[name] = s.g.rule_new(lhs, rhs)

		if type(action) != tuple:
			action = (action,)
		s.actions[r] = action
		return r

	def sequence(s,name, lhs, rhs, action=ident, separator=-1, min=1, proper=False):
		assert type(name) in str_and_uni
		assert name not in s.rules._dict
		assert type(lhs) == symbol_int

		assert type(rhs) == symbol_int
		r = s.rules[name] = s.g.sequence_new(lhs, rhs, separator, min, proper)

		if type(action) != tuple:
			action = (action,)
		s.actions[r] = action
		return r

	def known(s,char):
		"""create a symbol for a char"""
		if not char in s.known_chars:
			s.known_chars[char] = s.symbol(char)
		return s.known_chars[char]

	def known_string(s, string):
		"""create a symbol for a string"""
		rhs = [s.known(i) for i in string]
		lhs = s.symbol(s)
		s.rule(string, lhs, rhs, join)
		return lhs

	def set_start_symbol(s,start):
		s.g.start_symbol_set(start)

	def raw2tokens(s,raw):
		"""return a list with known chars substituted with their corresponding symbol ids"""
		tokens = []
		for i, char in enumerate(raw):
			if char in s.known_chars:
				symid=s.known_chars[char]
			else:
				symid=s.syms.any
			tokens.append(symid)
		return tokens

	@staticmethod
	def sorted_by_values(dotdict):
		return sorted(dotdict._dict.items(),key=operator.itemgetter(1))

	def print_syms(s):
		log('syms:%s'%s.sorted_by_values(s.syms))

	def print_rules(s):
		log('rules:%s'%s.sorted_by_values(s.rules))

	def check_accessibility(s):
		for i in s.syms._dict.items():
			if not s.g.symbol_is_accessible(i[1]):
				log("inaccessible: %s (%s)"%i)

