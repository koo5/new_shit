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

def ignore(args):
	return None

class HigherMarpa(object):
	def __init__(s, debug=False):
		"""create a new grammar object and stuff"""
		s.syms = dotdict()
		s.g = Grammar()
		s.known_chars = {}
		s.actions = {} # per-rule valuator callbacks (functions that the parser steps loop calls to actually create basic values or Nodes from lists of values or child nodes
		if debug:
			s.symbol = s.named_symbol
			s.rules = dotdict()
			s.rule = s._rule_debug
			s.sequence = s._sequence_debug
		else:
			s.rule = s._rule_fast
			s.sequence = s._sequence_fast

	def named_symbol(s,name):
		"""create a symbol and save it in syms"""
		r = s.g.symbol_new()
		if name in s.syms._dict:
			raise Exception("%s already in syms"%name)
		s.syms[name] = r
		return r

	def unnamed_symbol(s,name):
		return s.symbol(str(r)+'_'+name)

	def symbol(s,name):
		return s.g.symbol_new()

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

	def _rule(s, lhs,rhs,action=ident):
		assert type(lhs) == symbol_int

		if type(rhs) != list:
			assert type(rhs) == symbol_int
			rhs = [rhs]

		r = s.g.rule_new(lhs, rhs)
		s._add_action(r, action)

		return r

	def _add_action(s, rule, action):
		if type(action) != tuple:
			action = (action,)
		s.actions[rule] = action


	def _rule_debug(s,name, lhs,rhs,action=ident):
		assert type(name) in str_and_uni
		assert name not in s.rules._dict
		r = s.rules[name] = s._rule(lhs,rhs,action)

	def _rule_fast(s,name, lhs,rhs,action=ident):
		return s._rule(lhs,rhs,action)


	def _sequence(s,lhs, rhs, action=ident, separator=-1, min=1, proper=False):
		assert type(lhs) == symbol_int
		assert type(rhs) == symbol_int
		r = s.g.sequence_new(lhs, rhs, separator, min, proper)
		s._add_action(r, action)

	def _sequence_debug(s,name, lhs, rhs, action=ident, separator=-1, min=1, proper=False):
		assert type(name) in str_and_uni
		assert name not in s.rules._dict

		r = s.rules[name] = s._sequence(lhs, rhs, action, separator, min, proper)
		return r

	def _sequence_fast(s,name, lhs, rhs, action=ident, separator=-1, min=1, proper=False):
		return s._sequence(lhs, rhs, action, separator, min, proper)

	def known_char(s,char):
		"""create a symbol for a char"""
		if not char in s.known_chars:
			r = s.known_chars[char] = s.symbol(char)
			assert r!= -1
			s.rule(char+"_is_known_char", s.syms.known_char, r)
		return s.known_chars[char]

	def known_string(s, string):
		"""create a symbol for a string"""
		rhs = [s.known_char(i) for i in string]
		lhs = s.symbol(string)
		s.rule(str(lhs)+'_'+string, lhs, rhs, join)
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
				symid=s.syms.nonspecial_char
			tokens.append(symid)
		return tokens

	@staticmethod
	def sorted_by_values(dotdict):
		return sorted(dotdict._dict.items(),key=operator.itemgetter(1))

	def print_syms(s):
		log('syms:%s'%s.sorted_by_values(s.syms))

	def print_rules(s):
		#log('rules:%s'%s.sorted_by_values(s.rules))
		log('rules:')
		for r in s.sorted_by_values(s.rules):
			log(r)

	def check_accessibility(s):
		for i in s.syms._dict.items():
			if not s.g.symbol_is_accessible(i[1]):
				log("inaccessible: %s (%s)"%i)

