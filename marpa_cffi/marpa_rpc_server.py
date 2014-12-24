

from pizco import Server


# region marpa

import marpa_cffi
marpa = marpa_cffi.try_loading_marpa()
if marpa == True:
	from marpa_cffi.marpa_rpc_client import *
	import marpa_cffi.marpa_codes
	import marpa_cffi.graphing_wrapper as graphing_wrapper
else:
	log(marpa)
	log('no marpa, no parsing!')
	if not args.lame:
		log("install libmarpa or run with --lame")
		raise marpa
	else:
		marpa = False



def parse(raw): #just text now, list_of_texts_and_nodes later

	tokens = m.raw2tokens(raw)

m = MarpaClient()


def setup_grammar(root,scope):
	global m

	assert scope == uniq(scope)

	for i in root.flatten():
		i.forget_symbols()

	m = HigherMarpa(args.graph_grammar or args.log_parsing)

	if args.graph_grammar:
		graphing_wrapper.start()
		graphing_wrapper.symid2name = m.symbol2name

	m.named_symbol('start')
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

	m.set_start_symbol(m.syms.start)

	if args.log_parsing:
		log(m.syms_sorted_by_values)
		log(m.rules)

	m.g.precompute()

	m.check_accessibility()


# endregion



class RpcServer(object):


	def precompute(s, inp):
		inp = dotdict(inp)

		s.g = Grammar()

		"""
		keys of inp:
			num_symbols: how many symbols to allocate





		"""


		# this calls symbol_new() repeatedly inp.num_syms times, and gathers the
		# results in a list
		s.syms = list(starmap(g.symbol_new(), ((), inp.num_syms)))
		# this is too smart. also, todo: make symbol_new throw exceptions



	def parse(s, tokens):

		r = Recce(m.g)
		r.start_input()

		for i, sym in enumerate(tokens):
			if args.log_parsing:
				log ("input:symid:%s name:%s raw:%s"%(sym, m.symbol2name(sym),raw[i]))
			assert type(sym) == symbol_int
			r.alternative(sym, i+1)
			r.earleme_complete()

		#token value 0 has special meaning(unvalued), so lets i+1 over there and insert a dummy over here
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

	@topic2
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



server = Server(RpcServer())
server.serve_forever()
