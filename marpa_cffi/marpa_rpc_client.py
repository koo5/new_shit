import operator
import types
from queue import Queue
import threading
from itertools import starmap, repeat

from lemon_utils.dotdict import Dotdict
from lemon_utils.lemon_six import unicode, itervalues
from lemon_utils.utils import uniq
from lemon_args import args

import marpa_cffi
marpa = marpa_cffi.try_loading_marpa()
if marpa == True:
	import marpa_cffi.marpa_codes
	import marpa_cffi.graphing_wrapper as graphing_wrapper
	from marpa_cffi.marpa import *
	from marpa_cffi.marpa_misc import *
else:
	log(marpa)
	log('no marpa, no parsing!')
	if not args.lame:
		log("install libmarpa or run with --lame")
		raise marpa
	else:
		marpa = False






class ThreadedMarpa(object):
	def __init__(s, debug=True):
		s.debug = debug
		s.syms = Dotdict()
		if debug:
			s.debug_sym_names = []
		s.num_syms = 0
		s.known_chars = {}
		s.rules = []
		#---
		s.t = MarpaThread()
		s.t.start()
		s.cancel = False

	def named_symbol(s,name):
		"""create a symbol and save it in syms with the name as key"""
		if name in s.syms._dict:
			raise Exception("%s already in named_syms"%name)
		r = s.syms[name] = s.symbol(name)
		return r

	def symbol(s,debug_name):
		if s.debug:
			s.debug_sym_names.append(debug_name)
		r = symbol_int(s.num_syms) # starting with 0
		s.num_syms += 1
		return r

	def symbol2debug_name(s,symid):
		assert s.debug
		return s.debug_sym_names[symid]

	def rule2debug_name(s,r):
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
			assert type(action) in (types.FunctionType, types.MethodType)

		s.rules.append((False, debug_name, lhs, rhs, action))

	def sequence(s,debug_name, lhs, rhs, action=ident, separator=-1, min=1, proper=False):
		assert type(lhs) == symbol_int
		assert type(rhs) == symbol_int
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

	def known_string(s, string):
		"""create a symbol for a string"""
		rhs = [s.known_char(i) for i in string]
		lhs = s.symbol(string)
		s.rule(string+'_is_known_string', lhs, rhs, join)
		return lhs

	def string2tokens(s,raw):
		"""return a list with known chars substituted with their corresponding symbol ids"""
		tokens = []
		for i, char in enumerate(raw):
			try:
				symid=s.known_chars[char]
			except IndexError:
				symid=s.debug_sym_names.nonspecial_char
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


	def parse(raw):
		#just text now, list_of_texts_and_nodes later
		tokens = m.raw2tokens(raw)

	def collect_grammar(s,scope:list):
		assert scope == uniq(scope)

		s.named_symbol('start')
		#s.set_start_symbol(s.syms.start)
		s.named_symbol('nonspecial_char')
		s.named_symbol('known_char')
		s.named_symbol('maybe_spaces')
		s.sequence('maybe_spaces', s.syms.maybe_spaces, s.known_char(' '), action=ignore, min=0)

		for i in scope:
			#the property is accessed here, forcing the registering of the nodes grammars
			sym = i.symbol
			if sym != None:
				if args.log_parsing:
					log(sym)
					rulename = 'start is %s' % s.symbol2name(sym)
				else:
					rulename = ""
				s.rule(rulename , s.syms.start, sym)
				#maybe could use an action to differentiate a full parse from ..what? not a partial parse, because there would have to be something starting with every node

	def queue_precomputation(s, for_node):
		s.t.input.put(Dotdict(
			task = 'feed',
			num_syms = s.num_syms,
			rules = s.rules[:],
			for_node = for_node,
			start=s.syms.start))


class LoggedQueue(Queue):
	def put(s, x):
		log(x)
		super().put(x)

class MarpaThread(threading.Thread):
	def __init__(s):
		super().__init__(daemon=True)
		s.input = LoggedQueue()
		s.output = LoggedQueue()


	def run(s):
		"""https://groups.google.com/forum/#!topic/marpa-parser/DzgMMeooqT4
		imho unbased requirement that all operations are done in one thread..so
		lets make a litte event loop here"""
		while True:
			inp = s.input.get()
			if inp.task == 'feed':
				s.feed(inp)
			elif inp.task == 'parse':
				s.output.put(Dotdict(message = 'parsed', results = list(s.parse(inp.tokens))))


	def feed(s, inp):
		s.g = Grammar()
		# this calls symbol_new() repeatedly inp.num_syms times, and gathers the
		# results in a list # this is too smart. also, todo: make symbol_new throw exceptions
		s.c_syms = list(starmap(s.g.symbol_new, repeat(tuple(), inp.num_syms)))
		log('s.c_syms:%s',s.c_syms)
		s.g.start_symbol_set(s.c_syms[inp.start])
		s.c_rules = []
		for rule in inp.rules:
			if rule[0]: # its a sequence
				_, _, lhs, rhs, action, sep, min, prop = rule
				s.c_rules.append(s.g.sequence_new(lhs, rhs, sep, min, prop))
			else:
				_, _, lhs, rhs, _ = rule
				s.c_rules.append(s.g.rule_new(lhs, rhs))

		s.g.precompute()
		#check_accessibility()
		s.output.put(Dotdict(message = 'precomputed', for_node = inp.for_node))


	def parse(s, tokens):

		r = Recce(s.g)
		r.start_input()

		for i, sym in enumerate(tokens):
			#if args.log_parsing:
			#	log ("input:symid:%s name:%s raw:%s"%(sym, m.symbol2name(sym),raw[i]))
			#assert type(sym) == symbol_int
			r.alternative(s.c_syms[sym], i+1)
			r.earleme_complete()

		#token value 0 has special meaning(unvalued),
		# so lets i+1 over there and prepend a dummy
		tokens.insert(0,'dummy')

		latest_earley_set_ID = r.latest_earley_set()
		log ('latest_earley_set_ID=%s'%latest_earley_set_ID)

		try:
			b = Bocage(r, latest_earley_set_ID)
		except:
			return # no parse

		o = Order(b)
		tree = Tree(o)

		for _ in tree.nxt():
			r=do_steps(tree, tokens, raw)
			yield r

	def do_steps(tree, tokens, raw):
		stack = defaultdict((lambda:evil('default stack item, what the beep')))
		stack2= defaultdict((lambda:evil('default stack2 item, what the beep')))
		v = Valuator(tree)
		babble = False

		while True:
			s = v.step()
			if babble:
				log  ("stack:%s"%dict(stack))#convert ordereddict to dict to get neater __repr__
				log ("step:%s"%codes.steps2[s])
			if s == lib.MARPA_STEP_INACTIVE:
				break

			elif s == lib.MARPA_STEP_TOKEN:

				pos = v.v.t_token_value - 1
				sym = symbol_int(v.v.t_token_id)

				assert v.v.t_result == v.v.t_arg_n

				char = raw[pos]
				where = v.v.t_result
				if babble:
					log ("token %s of type %s, value %s, to stack[%s]"%(pos, symbol2name(sym), repr(char), where))
				stack[where] = stack2[where] = char

			elif s == lib.MARPA_STEP_RULE:
				r = v.v.t_rule_id
				#print ("rule id:%s"%r)
				if babble:
					log ("rule:"+rule2name(r))
				arg0 = v.v.t_arg_0
				argn = v.v.t_arg_n

				#args = [stack[i] for i in range(arg0, argn+1)]
				#stack[arg0] = (rule2name(r), args)


				actions = m.actions[r]


				val = [stack2[i] for i in range(arg0, argn+1)]

				if args.log_parsing:
					debug_log = str(m.rule2name(r))+":"+str(actions)+"("+repr(val)+")"

				try:
					for action in actions:
						val = action(val)
						if args.log_parsing:
							debug_log += '->'+repr(val)
				finally:
					if args.log_parsing:
						log(debug_log)

				stack2[arg0] = val

			elif s == lib.MARPA_STEP_NULLING_SYMBOL:
				stack2[v.v.t_result] = "nulled"
			elif s == lib.MARPA_STEP_INACTIVE:
				log("MARPA_STEP_INACTIVE:i'm done")
			elif s == lib.MARPA_STEP_INITIAL:
				log("MARPA_STEP_INITIAL:stating...")
			else:
				log(marpa_cffi.marpa_codes.steps[s])

		v.unref()#promise me not to use it from now on
		#print "tada:"+str(stack[0])
	#	print ("tada:"+json.dumps(stack[0], indent=2))
		#log ("tada:"+json.dumps(stack2[0], indent=2))
		res = stack2[0] # in position 0 is final result
		log ("tada:"+repr(res))
		return res










	"""
	<jeffreykegler> By the way, a Marpa parser within a Marpa parser is a strategy pioneered by Andrew Rodland (hobbs) and it is the way that the SLIF does its lexing -- the SLIF lexes by repeatedly creating Marpa subgrammars, getting the lexeme, and throwing away the subgrammar.
	"""
"""
		if args.graph_grammar:
			graphing_wrapper.start()
			graphing_wrapper.symid2name = m.symbol2name

		if args.graph_grammar:
			graphing_wrapper.generate_gv()
			graphing_wrapper.stop()

		if args.log_parsing:
			log(m.syms_sorted_by_values)
			log(m.rules)
"""