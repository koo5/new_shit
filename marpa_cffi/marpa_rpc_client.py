"""
job:
currently not really a rpc client, it just spawns a thread
MarpaThread needs to become a standalone program. The two parts already communicate over json,
but we need to do a little more untangling:
valuator "actions": functions like join or ident. we need to store them in ThreadedMarpa,
and MarpaThread must only pass back what to call.
"""

from typing import *
int

import sys, traceback
import operator
import types
import collections

import logging
logger=logging.getLogger("marpa")
log=logger.debug
info=logger.info

from lemon_utils.dotdict import Dotdict

from lemon_utils.lemon_six import unicode, iteritems
from lemon_utils.utils import uniq
from lemon_args import args

if args.log_parsing:
	logger.setLevel("DEBUG")


from marpa_cffi.marpa_thread import MarpaThread
import marpa_cffi.valuator_actions as valuator_actions
import marpa_cffi.graphing_wrapper as graphing_wrapper
from .marpa_misc import *

class MarpaClient(object):
	def __init__(s, send_thread_message, debug=True):
		s.send_thread_message = send_thread_message
		s.debug = debug
		s.clear()

	def clear(s):
		s.node_rules = {}
		s.node_symbols = {}
		if s.debug:
			s.debug_sym_names = []
		s.syms = Dotdict()
		s.num_syms = 0
		s.known_chars = {}
		s.rules = []
		s.symbol_ranks = {}
		s._parser_symbol = None
		s.excepts = {}

	#def kill(s):


	def set_symbol_rank(s, sy, r):
		s.symbol_ranks[sy] = r

	def named_symbol(s,name):
		"""create a symbol and save it in syms with the name as key"""
		if name in s.syms._dict:
			raise Exception("%s already in named_syms"%name)
		r = s.syms[name] = s.symbol(name)
		return r

	def symbol(s,debug_name):
		if s.debug:
			s.debug_sym_names.append(graphing_wrapper.escape_symbol_name_for_readable_printing(debug_name))
		r = symbol_int(s.num_syms) # starting with 0
		s.num_syms += 1
		return r

	def symbol2debug_name(s,symid):
		if s.debug:
			if symid < len(s.debug_sym_names):
				return s.debug_sym_names[symid]
			else:
				assert False
		return str(symid)

	def rule2debug_name(s,r):
		assert s.debug
		return s.rules[r]

	def rule(s,debug_name, lhs,rhs,action=valuator_actions.ident, rank=0):
		if type(rhs) != list:
			rhs = [rhs]

		if __debug__:
			assert type(lhs) == symbol_int,        lhs
			for i in rhs:
				assert type(i) == symbol_int
			assert type(debug_name) == unicode
			assert type(action) in (tuple, types.FunctionType, types.MethodType)

		log((debug_name, lhs, rhs, action, rank))
		rule = (False, debug_name, lhs, rhs, action, rank)
		if not rule in s.rules:
			s.rules.append(rule)

	def sequence(s,debug_name, lhs, rhs, action=valuator_actions.ident, separator=-1, min=1, proper=False):
		assert type(lhs) == symbol_int
		assert type(rhs) == symbol_int
		assert (type(separator) in (int, symbol_int)),    type(separator)
		assert type(min) == int
		assert type(proper) == bool
		assert type(debug_name) == unicode
		s.rules.append((True, debug_name, lhs, rhs, action, separator, min, proper))

	def known_char(s, char):
		"""create a symbol for a single char"""
		try:
			return s.known_chars[char]
		except KeyError:
			r = s.known_chars[char] = s.symbol(char)
			s.rule(char+"_is_known_char", s.syms.known_char, r)
			return r

	def known_char_except(s, e):
		if e not in s.excepts:
			s.excepts[e] = s.symbol("except "+e)
		return s.excepts[e]

	def known_string(s, string):
		"""create a symbol for a string"""
		rhs = [s.known_char(i) for i in string]
		lhs = s.symbol(string)
		s.rule(string+'_is_known_string', lhs, rhs, valuator_actions.join)
		return lhs

	def string2tokens(s,raw):
		"""return a list with known chars substituted with their corresponding symbol ids
		see: known_char
		"""
		tokens = []
		for i, char in enumerate(raw):
			try:
				symid=s.known_chars[char]
			except KeyError:
				symid=s.syms.nonspecial_char
			tokens.append(symid)
		return tokens

	@staticmethod
	def sorted_by_values(dotdict):
		return sorted(dotdict._dict.items(),key=operator.itemgetter(1))

	@property
	def syms_sorted_by_values(s):
		return s.sorted_by_values(s.debug_sym_names)

	def check_accessibility(s):
		for i in s.debug_sym_names._dict.items():
			if not s.g.symbol_is_accessible(i[1]):
				raise Exception("inaccessible: %s (%s)"%i)
	#---------

	@property
	def parser_symbol(m):
		if m._parser_symbol == None:
			m._parser_symbol = m.symbol('parser')
			parser_one_char = m.symbol('parser_one_char')
			m.rule('parser1', parser_one_char, m.syms.nonspecial_char)
			m.rule('parser2', parser_one_char, m.syms.known_char)
			m.sequence('parser', parser, parser_one_char, min=0)
		return m._parser_symbol


	def collect_grammar(s, full_scope:list, scope:list, start=None):
		full_scope = full_scope[:]
		scope = scope[:]
		assert scope == uniq(scope),  (scope,uniq(scope))

		s.clear()
		log("collect_grammar:...")

		#we dont have a separate tokenizer
		#any char used in any terminal of the grammar:
		s.named_symbol('known_char')
		#all the rest:
		s.named_symbol('nonspecial_char')

		#these should eventually be defined in lemon lang
		s.named_symbol('maybe_spaces')
		s.sequence('maybe_spaces', s.syms.maybe_spaces, s.known_char(' '), action=valuator_actions.ignore, min=0)

		s.named_symbol('whitespace_char')
		s.named_symbol('maybe_whitespace')
		for x in ' \n\t':
			s.rule("whitespace_char", s.syms.whitespace_char, s.known_char(x))
		s.sequence('maybe_whitespace', s.syms.maybe_whitespace, s.syms.whitespace_char,action=valuator_actions.ignore, min=0)

		s.scope = scope
		#"anything" means we are parsing for the editor and want to parse any fragment of the language
		anything = start==None
		if anything:
			s.start=s.named_symbol('start')
		else:
			s.start = start.symbol(s)
		if s.debug:	log("start=%s", s.symbol2debug_name(s.start) )

		import nodes
		def is_relevant_for(s, scope):
			sub = s.ch.sub.parsed
			sup = s.ch.sup.parsed
			aa = nodes.deref_def(sub)
			bb = nodes.deref_def(sup)
			a = aa in scope
			b = bb in scope
			logging.getLogger("scope").debug("%s is_relevant_for scope? %s %s (%s, %s)", s.tostr(), a, b, aa, bb)
			return a and b

		for i in full_scope:
			if type(i).__name__ == "WorksAs":
				if is_relevant_for(i, scope):
					if not i in scope:
						scope.append(i)

		for i in scope:
			i.symbol(s)

		if anything:
			for i in scope:
				if i.symbol(s) != None:
					if args.log_parsing:
						if s.debug: log(i.symbol(s))
						rulename = 'start is %s' % s.symbol2debug_name(i.symbol(s))
					else:
						rulename = ""
					s.rule(rulename , s.start, i.symbol(s))

		s.worksas_magic(scope)
		s.anything_excepts()

	def worksas_magic(s, scope):
		#ok here we're gonna walk thru WorkAssess and BindsTighters and do the precedence and associativity magic
		# http://pages.cs.wisc.edu/~fischer/cs536.s08/course.hold/html/NOTES/3.CFG.html#prec
		# https://metacpan.org/pod/distribution/Marpa-R2/pod/Scanless/DSL.pod#priority
		"""
		so, i think we should walk thru all syntaxeds
		some appear in other nodes grammar literally, like a TypedParameter in a list_of(TypedParameter).
		for this reason, i would assign each syntaxed a symbol.
		Additionally, some are denoted with "*sub works as *sup", to work as, for example, an expression.
		presumably, there will be only one sup for any sub.
		"""
		worksases  = collections.defaultdict(list)
		asoc = collections.defaultdict(lambda: "left")
		pris = collections.defaultdict(lambda:  1000)
		worksases2 = collections.defaultdict(lambda: collections.defaultdict(list))
		log("magic:")
		import nodes
		simple = 1
		for n in scope:
			if n.__class__.__name__ == 'WorksAs':
				sup = n.ch.sup.parsed
				sub = n.ch.sub.parsed
				if not isinstance(sup, nodes.Ref) or not isinstance(sub, nodes.Ref):
					print("invalid sub or sup in worksas")
					return
				sup_target = sup.target
				sub_target = sub.target
				worksases[sup_target].append(sub_target)

				if simple:
					rule_lhs = sup_target.symbol(s)
					rule_rhs = sub_target.symbol(s)
					if args.log_parsing:
						log('%s worksas %s\n (%s := %s)'%(sub_target, sup_target, rule_lhs, rule_rhs))
					if rule_lhs != None and rule_rhs != None:
						r = s.rule(str(n), rule_lhs, rule_rhs)
					else:
						print('%s or %s is None'%(rule_lhs, rule_rhs))

			elif n.__class__.__name__ == 'HasPriority':
				k = deref_def(n.ch.node)
				assert k not in pris
				pris[k] = n.ch.value.pyval
			elif n.__class__.__name__ == 'HasAssociativity':
				k = deref_def(n.ch.node)
				assert k not in asoc
				asoc[k] = n.ch.value.pyval

		if simple:
			return

		for sup,subs in iteritems(worksases):
			for sub in subs:
				worksases2[sup][pris[sub]].append(sub)

		for sup, priority_levels in iteritems(worksases2):
			this_level = sup
			for level_index in range(len(priority_levels)):
				this_level = priority_levels[level_index]
				if level_index == len(priority_levels):
					next_level_index = 0
				else:
					next_level_index = level_index + 1
				next_level = priority_levels[next_level_index]	
				next_level_symbol = s.named_symbol(str(sup)+str(next_level_index))
				for sub in this_level:
					syntax = []
					for i in sub.syntax:
						if isinstance(i, TextTag):
							syntax.append(m.known_string(i.value))
						else:
							slot = sub.slots[i.value]
							if slot == sup:
								syntax.append(next_level_symbol)
							else:
								syntax.append(slot.symbol(m))
				sup = next_level


		"""
		for sup,levels in iteritems(worksas2):
			for level in levels:
				for sub in level:
					if asoc[node] == "left":
						rules[sup].append(
					if asoc[node] == "right":
		"""
		"""
		nodes = DefaultDict(list)
		asoc  = DefaultDict(lambda: "left")
		pris = DefaultDict(lambda: 1000)

		for n in scope:
			if n.__class__.__name__ in ['SyntaxedNodecl']:
				nodes.append(n)
			if n.__class__.__name__ == 'HasPriority':
				k = deref_def(n.ch.node)
				assert k not in pris
				pris[k] = n.ch.value.pyval
			if n.__class__.__name__ == 'HasAssociativity':
				k = deref_def(n.ch.node)
				assert k not in asoc
				asoc[k] = n.ch.value.pyval

		for sup,subs in iteritems(worksas):
			for sub in subs:
				worksas2[k][pris[v]].append(v)

		for sup,levels in iteritems(worksas2):
			for level in levels:
				for sub in level:
					if asoc[node] == "left":
						rules[sup].append(
					if asoc[node] == "right":
		"""
		"""
		worksas = DefaultDict(list)
		asoc  = DefaultDict(lambda: "left")
		pris = DefaultDict(lambda: 1000)
		
		for i in scope:
			if i.__class__.__name__ == 'WorksAs':
				worksas[i.ch.sup.target].append(i.ch.sub.target)
			if n.__class__.__name__ == 'HasPriority':
				k = deref_def(n.ch.node)
				assert k not in pris
				pris[k] = n.ch.value.pyval
			if n.__class__.__name__ == 'HasAssociativity':
				k = deref_def(n.ch.node)
				assert k not in asoc
				asoc[k] = n.ch.value.pyval
			
		for sup,subs in iteritems(worksas):
			for sub in subs:
				worksas2[k][pris[v]].append(v)
		
		for sup,levels in iteritems(worksas2):
			for level in levels:
				for sub in level:
					if asoc[node] == "left":
						rules[sup].append(
					if asoc[node] == "right":
		"""
		"""
		levels = {}
		import collections
		levels = collections.OrderedDict(sorted(levels.items()))
		for k,v 
		"""
		"""
		sups = DefaultDict(list)
		pris = DefaultDict(list)
		asoc = DefaultDict(-1)

		for i in scope:
			#sub._losers = []
			if i.__class__.__name__ == 'WorksAs':
				#sub WorksAS sup, these are Refs
				sups[i.ch.sup.target].append(i.ch.sub.target)

		for k,v in sups:
			for sub in v:
				for n in scope:
					if n.__class__.__name__ == 'HasPriority':
						pris[n.ch.value.pyval].append(n.ch.node)
					if n.__class__.__name__ == 'HasAssociativity':
						asoc[n.ch.value.pyval].append(n.ch.node)

		for k,v in sups:
			for sub in v:
				pri = pris[sub]
				if not pri in level_syms[sup]:
					level_syms[sup][pri] = s.symbol(sup.name + pri)
				lhs = level_syms[sup][pri]
				rhs =
				pris[sub]

		for k,v in sups:
			for sub in v:
				for n in scope:
					if n.__class__.__name__ == 'BindsTighterThan':
						if n.ch.b.target == sub:
							sub._tighter_ones.append(n.ch.a.target)

		for k, v in sups:
			for sub in v:
				level = 0
				while sub._losers
		"""
		#hmm how is this gonna mesh out with the "anything" rules and with autocompletion rules?

	def anything_excepts(s):
		for k, v in iteritems(s.excepts):
			for ch, sym in iteritems(s.known_chars):
				if ch != k:
					s.rule(ch + " is anything except "+k, v, [sym])

	def enqueue_precomputation(s, for_node):
		s.t = MarpaThread()
		s.t.send_thread_message = s.send_thread_message
		s.t.start()
		#while not s.t.input.empty():
		#	s.t.input.get(block=False)
		s.t.input.put(Dotdict(
			task = 'precompute_grammar',
			num_syms = s.num_syms,
			symbol_ranks = s.symbol_ranks,
			rules = s.rules[:],
			for_node = for_node,
			debug = s.debug,
			debug_sym_names = s.debug_sym_names[:] if s.debug else None,
			start=s.start))

	def enqueue_parsing(s, tr):
		s.t.input.put(Dotdict(
			task = 'parse',
			tokens = tr[0],
			raw = tr[1],
			rules = s.rules[:]))



#maybe could use an action to differentiate a full parse from ..what? not a partial parse, because there would have to be something starting with every node
#wat? anyway, i will need logpy for this i think
"""maybe we want to only make the start_is_something rules
when that something cant be reached from Statement thru WorksAs..
lets just prune the duplicate results for now"""
"""
parse_result = list(parse_result)
r2 = parse_result[:]
nope = []
for i,v in enumerate(parse_result):
	for susp in parse_result:
		if susp != v and v.eq_by_value(susp):
			nope.append(v)
parse_result = [i for i in parse_result if not i in nope]
"""#i dont feel like implementing eq_by_value for everything now


"""diosyncrat_> you can pull them out of the progress reports already.
<idiosyncrat_> you can also add nulling symbols and use nulling events
<idiosyncrat_> That is, before every nonterminal whose prediction is of interest ...
<idiosyncrat_> place a nulling symbol, and add a nulling event for it.
<idiosyncrat_> And you should be able to use prediction events.
<idiosyncrat_> Prediction events cannot be *marked* in the recognizer, only in the grammar, but ...
<idiosyncrat_> they can be *activitated* and *deactivated* in the recognizer.
<idiosyncrat_> (The reason for all this is there is some overhead per marked symbol for each event, so it pays to make the user declare which symbols he *might* want to use.  The user can then activate them and deactivate the events, depending on whether they actually want to see the events or not.)
"""


"""
<jeffreykegler> By the way, a Marpa parser within a Marpa parser is a strategy pioneered by Andrew Rodland (hobbs) and it is the way that the SLIF does its lexing -- the SLIF lexes by repeatedly creating Marpa subgrammars, getting the lexeme, and throwing away the subgrammar.
"""
"""
			

			graphing_wrapper.stop()

		if args.log_parsing:
			log(m.syms_sorted_by_values)
			log(m.rules)
"""

"""https://groups.google.com/forum/#!topic/marpa-parser/DzgMMeooqT4"""
