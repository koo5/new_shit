# coding=utf-8
from lemon_utils.lemmacsthread import LemmacsThread
from lemon_utils.lemon_six import iteritems


import logging
logger=logging.getLogger("marpa")
log=logger.debug
info=logger.info

import traceback, sys
from lemon_utils.dotdict import Dotdict
from itertools import starmap, repeat

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
from marpa_cffi.valuator_actions import *


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
					log("parsed %s results" % len(r))
					s.send(Dotdict(message='parsed', results=r))
			except Exception as e:
				traceback.print_exc(file=sys.stdout)
				s.send(Dotdict(message='eeerror', traceback=traceback.format_exc()))

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

		for k, v in iteritems(inp.symbol_ranks):
			s.g.symbol_rank_set(k, v)
			log(("symbol rank:", k, v))

		# if args.log_parsing:
		#	log('s.c_syms:%s',s.c_syms)
		s.g.start_symbol_set(s.c_syms[inp.start])
		s.c_rules = []
		for rule in inp.rules:
			log(rule)
			if rule[0]:  # its a sequence
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
				print("generate svg")
				graphviz.render('dot', 'svg', 'grammar.gv')
				graph = graphing_wrapper.generate2('grammar2', s.c_syms[inp.start])
				graphing_wrapper.generate_gv_dot(graph)
				print("generate svg")
				graphviz.render('dot', 'svg', 'grammar2.gv')

			import threading
			thr = threading.Thread(target=gen)
			thr.run()

		if s.g.precompute() == -2:
			s.send(Dotdict(message='precompute error', for_node=inp.for_node))

		for x in s.c_syms:
			if not s.g.symbol_is_accessible(x):
				log("inaccessible symbol: %s " % s.symbol2debug_name(x))

		s.send(Dotdict(message='precomputed', for_node=inp.for_node))

	def print_completions(s, r):
		position = ffi.new('int*')
		origin = ffi.new('int*')
		Marpa_Rule_ID = None
		count = 0
		while Marpa_Rule_ID != -1:
			Marpa_Rule_ID = lib.marpa_r_progress_item(r.r, position, origin)
			if Marpa_Rule_ID != -1:
				log("progress_item:pos:%s origin:%s rule:%s" % (
				position[0], origin[0], s.rule2debug_name(Marpa_Rule_ID)))
				count += 1
		log("%s progress_items" % count)
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
		log("current earleme: %s" % ce)
		lib.marpa_r_progress_report_start(r.r, ce)

		for i, sym in enumerate(tokens):
			# assert type(sym) == symbol_int
			if s.debug:
				log("parsed so far:%s" % raw[:i])
			if sym == None:
				log("input:symid:%s name:%s raw:%s" % (sym, s.symbol2debug_name(sym), raw[i]))
				log("grammar not implemented, skipping this node")
			else:
				s.print_events()
				# s.print_completions(r)

				if s.debug:
					log("input:symid:%s name:%s raw:%s" % (sym, s.symbol2debug_name(sym), raw[i]))
				r.alternative(s.c_syms[sym], i + 1)
			r.earleme_complete()
		s.print_events()
		# token value 0 has special meaning(unvalued),
		# so lets i+1 over there and prepend a dummy
		tokens.insert(0, 'dummy')

		latest_earley_set_ID = r.latest_earley_set()
		if args.log_parsing:
			log('latest_earley_set_ID=%s' % latest_earley_set_ID)

		if latest_earley_set_ID == 0:
			return

		try:
			b = Bocage(r, latest_earley_set_ID)
		except:
			return  # no parse

		o = Order(b)
		s.g.check_int(lib.marpa_o_rank(o.o))
		tree = Tree(o)

		for _ in tree.nxt():
			r = s.do_steps(tree, tokens, raw, rules)
			yield r

	def do_steps(s, tree, tokens, raw, rules):
		stack = defaultdict((lambda: evil('default stack item, what the beep')))
		stack2 = defaultdict((lambda: evil('default stack2 item, what the beep')))

		v = Valuator(tree)
		babble = True

		while True:
			step = v.step()
			if babble:
				log("stack:%s" % dict(stack))  # convert ordereddict to dict to get neater __repr__
				log("step:%s" % codes.steps2[step])
			if step == lib.MARPA_STEP_TOKEN:

				pos = v.v.t_token_value - 1
				sym = symbol_int(v.v.t_token_id)

				assert v.v.t_result == v.v.t_arg_n

				char = raw[pos]
				where = v.v.t_result
				if babble:
					log("token %s of type %s, value %s, to stack[%s]" % (
					pos, s.symbol2debug_name(sym), repr(char), where))
				stack[where] = stack2[where] = char
			elif step == lib.MARPA_STEP_RULE:
				r = v.v.t_rule_id  # type:int
				# print ("rule id:%s"%r)`
				# if babble:
				#	log ("rule:"+str(s.rule2debug_name(r)))
				arg0 = v.v.t_arg_0
				argn = v.v.t_arg_n

				# args = [stack[i] for i in range(arg0, argn+1)]
				# stack[arg0] = (rule2name(r), args)

				if babble:
					log(rules[r])
				actions = rules[r][4]

				val = [stack2[i] for i in range(arg0, argn + 1)]

				if babble:
					debug_log = str(s.rule2debug_name(r)) + ":" + str(actions) + "(" + repr(val) + ")"

				try:
					if type(actions) != tuple:
						actions = (actions,)

					for action in actions:
						val = action(val)
						if babble:
							debug_log += '->' + repr(val)
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

		v.unref()  # promise me not to use it from now on
		# print "tada:"+str(stack[0])
		import json
		# print ("tada:"+json.dumps(stack[0], indent=2))
		# log ("tada:"+json.dumps(stack2[0], indent=2))
		res = stack2[0]  # in position 0 is final result
		return res

	def symbol2debug_name(s, symid):
		if s.debug:
			if symid < len(s.debug_sym_names):
				return s.debug_sym_names[symid]
			else:
				assert False
		return str(symid)

	def rule2debug_name(s, r):
		if s.debug:
			return s.rules[r]
		else:
			return "rule" + str(r)
