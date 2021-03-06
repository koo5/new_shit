
# aand a little test, same as in test0.py for now
def _test1():
	# based on the example at the end of https://metacpan.org/pod/Marpa::R2::Advanced::Thin
	class SimpleNamespace:
		def __init__(self, pairs):
			self.__dict__.update(pairs)
		def __repr__(self):
			keys = sorted(self.__dict__)
			items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
			return "{}({})".format(type(self).__name__, ", ".join(items))

	g = Grammar()


	sy = SimpleNamespace([(name, g.symbol_new()) for name in "S E op number".split()])
	g.start_symbol_set(sy.S)
	rules = SimpleNamespace([(name, g.rule_new(lhs, rhs)) for name, lhs, rhs in [
		('start', sy.S, [sy.E]),
		('op'    , sy.E, [sy.E, sy.op, sy.E]),
		('number' , sy.E, [sy.number])]])

	g.precompute()

	r = Recce(g)
	r.start_input()

	print (g)
	print (r)

	# tokens = [(sy.number, 2),(sy.op, '-'),(sy.number, 1),(sy.op, '*'),
	#	(sy.number, 3),(sy.op, '+'),(sy.number, 1)]
	raw = '9-8*7+6'
	tokens = []
	for i ,v in enumerate(raw):
		try:
			tokens.append((sy.number, int(raw[i])))
		except:
			tokens.append((sy.op, raw[i]))

	print ([(i[0], i[1]) for i in tokens])
	# print [(i[0].name, i[1]) for i in tokens]


	for i, (sym, val) in enumerate(tokens):
		r.alternative(sym, i+ 1, 1)
		r.earleme_complete()
	# token value 0 has special meaning(unvalued), so lets i+1 over there and insert a dummy over here
	tokens.insert(0, 'dummy')

	latest_earley_set_ID = r.latest_earley_set()
	# print latest_earley_set_ID
	b = Bocage(r, latest_earley_set_ID)
	o = Order(b)

	tree = Tree(o)
	import gc
	for i in tree.nxt():
		_do_steps(tree, tokens, rules)
		gc.collect()  # force unrefing of the valuator and stuff


from collections import defaultdict


def _do_steps(tree, tokens, rules):
	stack = defaultdict((lambda: 666))
	v = Valuator(tree)

	print()
	print(v.v)

	while True:
		s = v.step()
		print("stack:%s" % dict(stack))  # avoid ordereddict's __repr__
		print("step:%s" % codes.steps2[s])
		if s == lib.MARPA_STEP_INACTIVE:
			break

		elif s == lib.MARPA_STEP_TOKEN:

			tok_idx = v.v.t_token_value

			assert type(tokens[tok_idx][0]) == symbol_int
			# assert      tokens[tok_idx][0].s == v.v.t_token_id
			assert v.v.t_result == v.v.t_arg_n

			where = v.v.t_result
			# print "token %s of type %s, value %s, to stack[%s]"%(tok_idx, tokens[tok_idx][0].name, repr(tokens[tok_idx][1]), where)
			print("token %s of type %s, value %s, to stack[%s]" % (
			tok_idx, tokens[tok_idx][0], repr(tokens[tok_idx][1]), where))
			stack[where] = tokens[tok_idx][1]

		elif s == lib.MARPA_STEP_RULE:
			r = v.v.t_rule_id
			# print "rule id:%s"%r
			print("rule:" + [key for key, val in rules.__dict__.iteritems() if val == r][0])
			arg0 = v.v.t_arg_0
			argn = v.v.t_arg_n

			if r == rules.start:
				string, val = stack[argn]
				stack[arg0] = "%s = %s" % (string, val)

			elif r == rules.number:
				num = stack[arg0]
				stack[arg0] = (str(num), num)

			elif r == rules.op:
				lstr, lval = stack[arg0]
				op = stack[arg0 + 1]
				rstr, rval = stack[argn]
				print(stack[arg0], op, stack[argn])
				text = '(' + lstr + " " + op + " " + rstr + ')'
				if op == '+':
					res = lval + rval
				elif op == '-':
					res = lval - rval
				elif op == '*':
					res = lval * rval
				elif op == '/':
					res = lval / rval
				else:
					print(op + '???')
					return
				stack[arg0] = (text, res)
			else:
				print("wat, %s?" % r)
	print("tada:" + str(stack[0]))


if __name__ == "__main__":
	_test1()
