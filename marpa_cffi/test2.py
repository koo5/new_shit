from collections import defaultdict
from collections import namedtuple
from marpa import *
import sys; sys.path.append('..'); from dotdict import dotdict



g = Grammar()
any = g.symbol_new()
known_chars = {}

def rule(lhs,rhs):
	if rhs.type != list:
		rhs = [rhs]
	return g.rule_new(lhs, rhs)

def symbol():
	return g.symbol_new_int()

def known(char):
	if not char in known_chars:
		known_chars[char] = symbol()
	return known_chars[char]

def know2(char, lhs=None):
	known(char)
	g.rule_new(any, known(char))
	if lhs != None:
		g.rule_new(lhs, known(char))


digit = symbol()
for i in [chr(j) for j in range(ord('0'), ord('9')+1)]:
	know2(i, digit)

def sequence_new(lhs, rhs)

rules.digits_is_sequence_of_digit = g.sequence_new(digits, digit, separator = -2)

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

rules.do_x_times = rule(do_x_times, [known_string('do'), expression, known_string('times:')]






toktup = namedtuple("token", "symid position")



def raw2tokens(raw):
	tokens = []
	for i, char in enumerate(raw):
		if char in known_chars:
			symid=known_chars[i]
		else:
			symid=any
		tokens.append(toktup(symid, position=i)))
	return tokens


start = symbol()
start.start_symbol_set()
statement = symbol()

rules.start = rule(start, statement)
rules.expression_is_statement = rule(statement, expression)
rules.do_x_times_is_statment = rule(statement, do_x_times)


g.precompute()


def test2(raw):
	tokens = raw2tokens()

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

			tok_idx = v.v.t_token_value
			
			assert type(tokens[tok_idx][0]) == symbol_int
			assert      tokens[tok_idx][0].s == v.v.t_token_id
			assert v.v.t_result == v.v.t_arg_n
			
			where = v.v.t_result
			print "token %s of type %s, value %s, to stack[%s]"%(tok_idx, tokens[tok_idx][0].name, repr(tokens[tok_idx][1]), where)
			stack[where] = tokens[tok_idx][1]
	
		elif s == lib.MARPA_STEP_RULE:
			r = v.v.t_rule_id
			#print "rule id:%s"%r
			print "rule:"+[key for key,val in rules.__dict__.iteritems() if val.r == r][0]
			arg0 = v.v.t_arg_0
			argn = v.v.t_arg_n

			#args = stack[arg0:argn]
			#argn = stack[argn]

			if r == start_r:
				res = stack[argn]
			
			elif r == rules.number.r:
				num = stack[arg0]
				stack[arg0] = (str(num), num)
			
			elif r == rules.op.r:
				lstr, lval = stack[arg0]
				op = stack[arg0 + 1]
				rstr, rval = stack[argn]
				print stack[arg0], op, stack[argn]
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
					print op + '???'
					return
				stack[arg0] = (text, res)
			else:
				print "wat, %s?"%r
	print "tada:"+str(stack[0])


test2('9321-82*7+6')
test2('do34*4times:')
