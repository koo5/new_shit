from collections import defaultdict
from collections import namedtuple
from marpa import *
import sys; sys.path.append('..'); from dotdict import dotdict

def fresh():
	global rules, syms, g, known_chars, actions
	rules = dotdict()
	syms = dotdict()
	g = Grammar()
	symbol(any)
	known_chars = {}
	actions = []

def symbol(name):
	r = g.symbol_new_int()
	assert name not in syms
	syms[name] = r
	return r

def rule(name, lhs,rhs,action=(lambda x:x)):
	if rhs.type != list:
		rhs = [rhs]
	assert name not in rules
	r = rules[name] = g.rule_new(lhs, rhs)
	actions[r] = action
	return r

def known(char):
	if not char in known_chars:
		known_chars[char] = symbol(char)
	return known_chars[char]

def test0():
	symbol("banana")
	print syms.banana
	try:
		print syms.orange
		assert False
	except KeyError:
		pass
	rule("banana_is_a_fruit", symbol('fruit'), syms.banana)
	known2('X')
	print syms.X
	known2('Y', 'why')
	print syms._dict, rules._dict

fresh()
test0()

def sequence_new(lhs, rhs, separator=-1, min=1, proper=False):
	return sequence_new_int(lhs, rhs, separator, min, proper)


def setup():
	digit = symbol()
	for i in [chr(j) for j in range(ord('0'), ord('9')+1)]:
		rule(digit, known(i))

	rules.digits_is_sequence_of_digit = sequence_new(digits, digit)

	number = symbol()
	rules.number_is_digits = rule(number, digits)

	#
	#multiplication's syntax 1: ChildTag("A"), '*', ChildTag("B")
	#register_grammar:
	#	s.symbol = new_symbol()
	#	rhs = []
	#	for i in syntax:
	#		if i.type == ChildTag:
	#			rhs.append(s.ch[i.name].symbol)
	#		if i.type == str:
	#			rhs.append(known(i))
	#		...

	expression = symbol()
	rules.number_is_expression = rule(expression, number)

	multiplication = symbol()
	rules.multiplication = rule(multiplication, [expression, known('*'), expression])

	def known_string(s):
		rhs = [known(i) for i in s]
		lhs = symbol()
		return rule(lhs, rhs)

	do_x_times = symbol()

	rules.do_x_times = rule(do_x_times, [known_string('do'), expression, known_string('times:')])


	start = symbol()
	start.start_symbol_set()
	statement = symbol()

	rules.start = rule(start, statement)
	rules.expression_is_statement = rule(statement, expression)
	rules.do_x_times_is_statment = rule(statement, do_x_times)





toktup = namedtuple("token", "symid pos")



def raw2tokens(raw):
	tokens = []
	for i, char in enumerate(raw):
		if char in known_chars:
			symid=known_chars[i]
		else:
			symid=any
		tokens.append(toktup(symid, pos=i))
	return tokens



def test1(raw):
	tokens = raw2tokens()

	g.precompute()
	r = Recce(g)
	r.start_input()

	print g
	print r
	
	for i, (sym, pos) in enumerate(tokens):
		r.alternative(sym, i+1, 1)
		r.earleme_complete()
	#token value 0 has special meaning(unvalued), so lets i+1 over there and insert a dummy over here
	tokens.insert(0,'dummy') 
	
	latest_earley_set_ID = r.latest_earley_set()
	print 'latest_earley_set_ID=%'%latest_earley_set_ID

	b = Bocage(r, latest_earley_set_ID)
	o = Order(b)
	tree = Tree(o)

	import gc
	for dummy in tree.nxt():
		do_steps(tree, tokens, rules)
		gc.collect #force an unref of the valuator and stuff so we can move on to the next tree


def symbol2name(s):
	for k,v in symbols.__dict.iteritems():
		if v == s:
			return k
	assert False

def rule2name(r):
	for k,v in rules.__dict.iteritems():
		if v == r:
			return k
	assert False


def do_steps(tree, tokens, rules):
	stack = defaultdict((lambda:666))
	v = valuator(tree)

	print
	print v.v
	
	while True:
		s = v.step()
		print "stack:%s"%dict(stack)#convert ordereddict to dict to get neater __repr__
		print "step:%s"%codes.steps2[s]
		if s == lib.MARPA_STEP_INACTIVE:
			break
	
		elif s == lib.MARPA_STEP_TOKEN:

			sym, pos = tokens[v.v.t_token_value]
			
			assert type(sym) == symbol_int
			assert sym == v.v.t_token_id

			assert v.v.t_result == v.v.t_arg_n

			char = raw[pos-1]
			where = v.v.t_result
			print "token %s of type %s, value %s, to stack[%s]"%(pos, symbol2name(sym), repr(char), where)
			stack[where] = char
	
		elif s == lib.MARPA_STEP_RULE:
			r = v.v.t_rule_id
			#print "rule id:%s"%r
			print "rule:"+rule2name(r)
			arg0 = v.v.t_arg_0
			argn = v.v.t_arg_n

			args = stack[arg0:argn+1]

			res = (rule2name(r), action[r])

			stack[arg0] = res

	print "tada:"+str(stack[0])



fresh()
setup()
print syms._dict, rules._dict
test1('9321-82*7+6')
test1('do34*4times:')
