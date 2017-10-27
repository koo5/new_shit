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
from itertools import starmap, repeat

import logging
logger=logging.getLogger("marpa")
log=logger.debug
info=logger.info

from lemon_utils.dotdict import Dotdict
from lemon_utils.lemmacsthread import LemmacsThread
from lemon_utils.lemon_six import unicode, itervalues, iteritems
from lemon_utils.utils import uniq
from lemon_args import args
from marpa_cffi.marpa_misc import *

if args.log_parsing:
	logger.setLevel("DEBUG")

import marpa_cffi
marpa = marpa_cffi.try_loading_marpa()
if marpa == True:
	import marpa_cffi.marpa_codes
	import marpa_cffi.graphing_wrapper as graphing_wrapper
	from marpa_cffi.marpa import *
else:
	log(marpa)
	log('no marpa, no parsing!')
	if not args.lame:
		log("install cffi and libmarpa, or run with --lame")
		raise marpa
	else:
 		marpa = False


class MarpaClient(object):
	def __init__(s, send_thread_message, debug=True):
		s.send_thread_message = send_thread_message
		s.debug = debug
		s.clear()

		s.node_rules = {}
		s.node_symbols = {}
		s.forget_symbols()

	def clear(s):
		s.node_symbols.clear()
		s.node_rules.clear()
		if s.debug:
			s.debug_sym_names = []
		s.syms = Dotdict()
		s.num_syms = 0
		s.known_chars = {}
		s.rules = []
		s.symbol_ranks = {}
		s._parser_symbol = None

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

	def rule(s,debug_name, lhs,rhs,action=ident, rank=0):
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

	def sequence(s,debug_name, lhs, rhs, action=ident, separator=-1, min=1, proper=False):
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

	def known_string(s, string):
		"""create a symbol for a string"""
		rhs = [s.known_char(i) for i in string]
		lhs = s.symbol(string)
		s.rule(string+'_is_known_string', lhs, rhs, join)
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
		s.sequence('maybe_spaces', s.syms.maybe_spaces, s.known_char(' '), action=ignore, min=0)

		s.named_symbol('whitespace_char')
		s.named_symbol('maybe_whitespace')
		for x in ' \n\t':
			s.rule("whitespace_char", s.syms.whitespace_char, s.known_char(x))
		s.sequence('maybe_whitespace', s.syms.maybe_whitespace, s.syms.whitespace_char,action=ignore, min=0)

		s.scope = scope
		#"anything" means we are parsing for the editor and want to parse any fragment of the language
		anything = start==None
		if anything:
			s.start=s.named_symbol('start')
		else:
			s.start = start.symbol
		if s.debug:	log("start=%s", s.symbol2debug_name(s.start) )

		for i in full_scope:
			if type(i).__name__ == "WorksAs":
				if i.is_relevant_for(scope):
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

		#ok here we're gonna walk thru WorkAssess and BindsTighters and do the precedence and associativity magic
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



class MarpaThread(LemmacsThread):
	def __init__(s):
		super().__init__()
		if args.log_parsing:
			s.input.logger = s.output.logger = logging.getLogger("marpa_rpc_queue")
			pass
		if args.graph_grammar:
			graphing_wrapper.start()
			graphing_wrapper.symid2name = s.symbol2debug_name
			lib.rule_new = graphing_wrapper.rule_new

	def send(s, msg):
		s.send_to_main_thread(msg)

	def run(s):
		while True:
			try:
				inp = s.input.get()
				if inp.task == 'precompute_grammar':
					s.precompute_grammar(inp)
				elif inp.task == 'parse':
					r = list(s.parse(inp.tokens, inp.raw, inp.rules))
					log("parsed %s results"%len(r))
					s.send(Dotdict(message = 'parsed', results = r))
			except Exception as e:
				traceback.print_exc(file=sys.stdout)
				s.send(Dotdict(message = 'eeerror', traceback = traceback.format_exc()))

	def precompute_grammar(s, inp):
		log('precompute_grammar...')

		s.debug_sym_names = inp.debug_sym_names
		s.rules = inp.rules
		s.debug = inp.debug

		graphing_wrapper.clear()


		s.g = Grammar()
		# this calls symbol_new() repeatedly inp.num_syms times, and gathers the
		# results in a list # this is too smart. also, todo: make symbol_new throw exceptions
		s.c_syms = list(starmap(s.g.symbol_new, repeat(tuple(), inp.num_syms)))
		for x in s.c_syms:
			marpa_cffi.marpa.lib.marpa_g_symbol_is_completion_event_set(s.g.g, x, True)
			marpa_cffi.marpa.lib.marpa_g_symbol_is_prediction_event_set(s.g.g, x, True)



		for k,v in iteritems(inp.symbol_ranks):
			s.g.symbol_rank_set(k,v)
			log(("symbol rank:", k, v))
		
		#if args.log_parsing:
		#	log('s.c_syms:%s',s.c_syms)
		s.g.start_symbol_set(s.c_syms[inp.start])
		s.c_rules = []
		for rule in inp.rules:
			log(rule)
			if rule[0]: # its a sequence
				_, _, lhs, rhs, action, sep, min, prop = rule
				s.c_rules.append(s.g.sequence_new(lhs, rhs, sep, min, prop))
			else:
				_, _, lhs, rhs, _, rank = rule
				cr = s.g.rule_new(lhs, rhs)
				if cr != -2:
					s.c_rules.append(cr)
					if rank != 0:
						s.g.rule_rank_set(cr, rank)
						log(("rank ", rule, rank))

		if args.graph_grammar:
			def gen():
				graphing_wrapper.generate_bnf()
				graph = graphing_wrapper.generate('grammar')
				graphing_wrapper.generate_gv_dot(graph)
				import graphviz
				print ("generate svg")
				graphviz.render('dot', 'svg', 'grammar.gv')
				graph = graphing_wrapper.generate2('grammar2', s.c_syms[inp.start])
				graphing_wrapper.generate_gv_dot(graph)
				print("generate svg")
				graphviz.render('dot', 'svg', 'grammar2.gv')
			import threading
			thr = threading.Thread(target = gen)
			thr.run()


		if s.g.precompute() == -2:
			s.send(Dotdict(message = 'precompute error', for_node = inp.for_node))

		for x in s.c_syms:
			if not s.g.symbol_is_accessible(x):
				log("inaccessible symbol: %s "%s.symbol2debug_name(x))

		s.send(Dotdict(message = 'precomputed', for_node = inp.for_node))


	def print_completions(s, r):
		position = ffi.new('int*')
		origin = ffi.new('int*')
		Marpa_Rule_ID = None
		count = 0
		while Marpa_Rule_ID != -1:
			Marpa_Rule_ID = lib.marpa_r_progress_item ( r.r, position, origin )
			if Marpa_Rule_ID != -1:
				log("progress_item:pos:%s origin:%s rule:%s"%(position[0], origin[0], s.rule2debug_name(Marpa_Rule_ID)))
				count += 1
		log("%s progress_items"%count)
		return count

	def print_events(s):
		for event_type, event_value in s.g.events():
			if event_type == marpa_cffi.marpa.lib.MARPA_EVENT_SYMBOL_PREDICTED:
				log('predicted:%s:%s', event_value, s.symbol2debug_name(event_value))
			elif event_type == marpa_cffi.marpa.lib.MARPA_EVENT_SYMBOL_COMPLETED:
				log('completed:%s:%s', event_value, s.symbol2debug_name(event_value))
			else:
				log('event:%s, value:%s', events[event_type], event_value)

	def parse(s, tokens, raw, rules):
		log("parse..")
		r = Recce(s.g)
		r.start_input()

		ce = lib.marpa_r_current_earleme(r.r);
		log("current earleme: %s"% ce)
		lib.marpa_r_progress_report_start(r.r, ce)

		for i, sym in enumerate(tokens):
			#assert type(sym) == symbol_int
			if s.debug:
				log("parsed so far:%s" % raw[:i])
			if sym == None:
				log ("input:symid:%s name:%s raw:%s"%(sym, s.symbol2debug_name(sym),raw[i]))
				log("grammar not implemented, skipping this node")
			else:
				s.print_events()
				#s.print_completions(r)

				if s.debug:
					log ("input:symid:%s name:%s raw:%s"%(sym, s.symbol2debug_name(sym),raw[i]))
				r.alternative(s.c_syms[sym], i+1)
			r.earleme_complete()
		s.print_events()
		#token value 0 has special meaning(unvalued),
		# so lets i+1 over there and prepend a dummy
		tokens.insert(0,'dummy')

		latest_earley_set_ID = r.latest_earley_set()
		if args.log_parsing:
			log ('latest_earley_set_ID=%s'%latest_earley_set_ID)

		if latest_earley_set_ID == 0:
			return

		try:
			b = Bocage(r, latest_earley_set_ID)
		except:
			return # no parse

		o = Order(b)
		s.g.check_int(lib.marpa_o_rank(o.o))
		tree = Tree(o)

		for _ in tree.nxt():
			r=s.do_steps(tree, tokens, raw, rules)
			yield r

	def do_steps(s, tree, tokens, raw, rules):
		stack = defaultdict((lambda:evil('default stack item, what the beep')))
		stack2= defaultdict((lambda:evil('default stack2 item, what the beep')))

		v = Valuator(tree)
		babble = True

		while True:
			step = v.step()
			if babble:
				log  ("stack:%s"%dict(stack))#convert ordereddict to dict to get neater __repr__
				log ("step:%s"%codes.steps2[step])
			if step == lib.MARPA_STEP_TOKEN:

				pos = v.v.t_token_value - 1
				sym = symbol_int(v.v.t_token_id)

				assert v.v.t_result == v.v.t_arg_n

				char = raw[pos]
				where = v.v.t_result
				if babble:
					log ("token %s of type %s, value %s, to stack[%s]"%(pos, s.symbol2debug_name(sym), repr(char), where))
				stack[where] = stack2[where] = char
			elif step == lib.MARPA_STEP_RULE:
				r = v.v.t_rule_id#type:int
				#print ("rule id:%s"%r)`
				#if babble:
				#	log ("rule:"+str(s.rule2debug_name(r)))
				arg0 = v.v.t_arg_0
				argn = v.v.t_arg_n

				#args = [stack[i] for i in range(arg0, argn+1)]
				#stack[arg0] = (rule2name(r), args)

				if babble:
					log(rules[r])
				actions = rules[r][4]


				val = [stack2[i] for i in range(arg0, argn+1)]

				if babble:
					debug_log = str(s.rule2debug_name(r))+":"+str(actions)+"("+repr(val)+")"

				try:
					if type(actions) != tuple:
						actions = (actions, )

					for action in actions:
						val = action(val)
						if babble:
							debug_log += '->'+repr(val)
				finally:
					if babble:
						log(debug_log)

				stack2[arg0] = val

			elif step == lib.MARPA_STEP_NULLING_SYMBOL:
				stack2[v.v.t_result] = "nulled"
			elif step == lib.MARPA_STEP_INACTIVE:
				if args.log_parsing:
					log("MARPA_STEP_INACTIVE:i'm done")
				break
			elif step == lib.MARPA_STEP_INITIAL:
				if args.log_parsing:
					log("MARPA_STEP_INITIAL:starting...")
			else:
				if args.log_parsing:
					log(marpa_cffi.marpa_codes.steps[step])

		v.unref()#promise me not to use it from now on
		#print "tada:"+str(stack[0])
		import json
		#print ("tada:"+json.dumps(stack[0], indent=2))
		#log ("tada:"+json.dumps(stack2[0], indent=2))
		res = stack2[0] # in position 0 is final result
		return res


	def symbol2debug_name(s,symid):
		if s.debug:
			if symid < len(s.debug_sym_names):
				return s.debug_sym_names[symid]
			else:
				assert False
		return str(symid)

	def rule2debug_name(s,r):
		if s.debug:
			return s.rules[r]
		else:
			return "rule"+str(r)

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
