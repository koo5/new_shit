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


	#---------


	def parse(raw):
		#just text now, list_of_texts_and_nodes later
		tokens = m.raw2tokens(raw)

	def setup_grammar(root,scope):
		assert scope == uniq(scope)

		for i in root.flatten():
			i.forget_symbols()

		if args.graph_grammar:
			graphing_wrapper.start()
			graphing_wrapper.symid2name = m.symbol2name

		m.named_symbol('start')
		m.set_start_symbol(m.syms.start)
		m.named_symbol('nonspecial_char')
		m.named_symbol('known_char')

		m.named_symbol('maybe_spaces')
		m.sequence('maybe_spaces', m.syms.maybe_spaces, m.known_char(' '), action=ignore, min=0)

		for i in scope:
			#the property is accessed here, forcing the registering of the nodes grammars
			sym = i.symbol
			if sym != None:
				if args.log_parsing:
					log(sym)
					rulename = 'start is %s' % m.symbol2name(sym)
				else:
					rulename = ""
				m.rule(rulename , m.syms.start, sym)
				#maybe could use an action to differentiate a full parse from ..what? not a partial parse, because there would have to be something starting with every node

		if args.graph_grammar:
			graphing_wrapper.generate_gv()
			graphing_wrapper.stop()

		if args.log_parsing:
			log(m.syms_sorted_by_values)
			log(m.rules)

	def precompute(s):

		s.server.precompute({
			'num_syms':len(s.syms),


		m.g.precompute()

		m.check_accessibility()





	"""
	<jeffreykegler> By the way, a Marpa parser within a Marpa parser is a strategy pioneered by Andrew Rodland (hobbs) and it is the way that the SLIF does its lexing -- the SLIF lexes by repeatedly creating Marpa subgrammars, getting the lexeme, and throwing away the subgrammar.
	"""