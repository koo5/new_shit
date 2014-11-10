#another experiment, a bit higher level, tokenizer-less, and lemon-oriented

from __future__ import unicode_literals
from __future__ import print_function

from collections import defaultdict
from collections import namedtuple
from marpa import *
import sys; sys.path.append('..')
from dotdict import dotdict
from lemon_logger import topic, log

def ident(x):
	return x

@topic('fresh')
def fresh():
	global rules, syms, g, known_chars, actions
	rules = dotdict()
	syms = dotdict()
	g = Grammar()
	known_chars = {}
	actions = {} # per-rule valuator functions

def symbol(name):
	r = g.symbol_new()
	assert name not in syms._dict
	syms[name] = r
	return r

def rule(name, lhs,rhs,action=(lambda x:x)):
	assert type(name) == str
	assert type(lhs) == symbol_int
	if type(rhs) != list:
		assert type(rhs) == symbol_int
		rhs = [rhs]
	assert name not in rules._dict
	r = rules[name] = g.rule_new(lhs, rhs)
	actions[r] = action
	return r


def symbol2name(s):
	for k,v in syms._dict.items():
		if v == s:
			return k
	assert False

def rule2name(r):
	for k,v in rules._dict.items():
		if v == r:
			return k
	assert False


def sequence(name, lhs, rhs, action=(lambda x:x), separator=-1, min=1, proper=False,):
	assert type(name) == str
	assert type(lhs) == symbol_int
	assert type(rhs) == symbol_int
	assert name not in rules._dict
	r = rules[name] = g.sequence_new(lhs, rhs, separator, min, proper)
	actions[r] = action
	return r

def known(char):
	if not char in known_chars:
		known_chars[char] = symbol(char)
	return known_chars[char]

def known_string(s):
	rhs = [known(i) for i in s]
	lhs = symbol(s)
	rule(s, lhs, rhs)
	return lhs


@topic('test0')
def test0():
	symbol("banana")
#	print syms.banana
	try:
		xxx = syms.orange
		assert False
	except KeyError:
		pass
	rule("banana_is_a_fruit", symbol('fruit'), syms.banana)
	known('X')
	known('Y')
	rule( 'why',syms.X, syms.Y)
	log("test0:", syms._dict, rules._dict)

fresh()
test0()


@topic('setup')
def setup():
	log("SETUP")

	symbol('start')
	symbol('any')
	g.start_symbol_set(syms.start)
	symbol('statement')
	rule('start', syms.start, syms.statement)
	symbol('expression')
	rule('expression_is_statement', syms.statement, syms.expression)

	symbol('digit')
	symbol('digits')
	for i in [chr(j) for j in range(ord('0'), ord('9')+1)]:
		rule(i + "_is_a_digit",syms.digit, known(i))

	sequence('digits_is_sequence_of_digit', syms.digits, syms.digit)
	symbol('number')
	rule('digits_is_number', syms.number, syms.digits)
	rule('number_is_expression',syms.expression, syms.number)

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

	symbol('string_body')
	symbol('string')
	sequence('string_body_is_sequence_of_any', syms.string_body, syms.any)
	rule('string', syms.string, [known("'"), syms.string_body, known("'")])
	rule('string_is_expression', syms.expression, syms.string)

	symbol('multiplication')
	rule('multiplication', syms.multiplication, [syms.expression, known('*'), syms.expression])
	rule('multiplication_is_expression',syms.expression, syms.multiplication)

	symbol('do_x_times')
	rule('do_x_times',syms.do_x_times, [known_string('do'), syms.expression, known_string('times:')])
	#rule('do_x_times_is_expression',syms.expression, syms.do_x_times)
	rule('do_x_times_is_statement',syms.statement, syms.do_x_times)








def raw2tokens(raw):
	tokens = []
	for i, char in enumerate(raw):
		if char in known_chars:
			symid=known_chars[char]
		else:
			symid=syms.any
		tokens.append(symid)
	return tokens



def test1(raw):
	tokens = raw2tokens(raw)

	g.precompute()

	for i in syms._dict.items():
		if not g.symbol_is_accessible(i[1]):
			print ("inaccessible: %s (%s)"%i)

	r = Recce(g)
	r.start_input()

	print ("TEST1")
	print (g)
	print (r)
	
	for i, sym in enumerate(tokens):
		print (sym, i+1, symbol2name(sym),raw[i])
		assert type(sym) == symbol_int
		r.alternative_int(sym, i+1)
		r.earleme_complete()
	
	log('ok')
	#token value 0 has special meaning(unvalued), so lets i+1 over there and insert a dummy over here
	tokens.insert(0,'dummy') 
	
	latest_earley_set_ID = r.latest_earley_set()
	print ('latest_earley_set_ID=%s'%latest_earley_set_ID)

	b = Bocage(r, latest_earley_set_ID)
	o = Order(b)
	tree = Tree(o)

	import gc
	for dummy in tree.nxt():
		do_steps(tree, tokens, raw, rules)
		gc.collect() #force an unref of the valuator and stuff so we can move on to the next tree


@topic('do steps')
def do_steps(tree, tokens, raw, rules):
	stack = defaultdict((lambda:666))
	v = Valuator(tree)
	babble = False
	print()
	print (v.v)
	
	while True:
		s = v.step()
		if babble:
			print ("stack:%s"%dict(stack))#convert ordereddict to dict to get neater __repr__
			print ("step:%s"%codes.steps2[s])
		if s == lib.MARPA_STEP_INACTIVE:
			break
	
		elif s == lib.MARPA_STEP_TOKEN:

			pos = v.v.t_token_value - 1
			sym = symbol_int(v.v.t_token_id)

			assert v.v.t_result == v.v.t_arg_n

			char = raw[pos]
			where = v.v.t_result
			if babble:
				print ("token %s of type %s, value %s, to stack[%s]"%(pos, symbol2name(sym), repr(char), where))
			stack[where] = char
	
		elif s == lib.MARPA_STEP_RULE:
			r = v.v.t_rule_id
			#print ("rule id:%s"%r)
			if babble:
				print ("rule:"+rule2name(r))
			arg0 = v.v.t_arg_0
			argn = v.v.t_arg_n

			args = [stack[i] for i in range(arg0, argn+1)]
			res = (rule2name(r), actions[r](args))

			stack[arg0] = res

	#print "tada:"+str(stack[0])
	import json
	print ("tada:"+json.dumps(stack[0], indent=2))

import operator

fresh()
setup()
print ('syms:%s'%sorted(syms._dict.items(),key=operator.itemgetter(1)))
print ('rules:%s'%sorted(rules._dict.items(),key=operator.itemgetter(1)))
#test1('9321-82*7+6')
test1('do34*4times:')
