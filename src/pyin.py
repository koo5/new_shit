#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from weakref import ref as weakref
#import rdflib
#from rdflib import Graph
import sys
#import common_utils
#g = common_utils.parse_input()
import logging
import urllib.parse

formatter = logging.Formatter('#%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console_debug_out = logging.StreamHandler()
console_debug_out.setFormatter(formatter)

logger=logging.getLogger()
#logger.addHandler(console_debug_out)
logger.setLevel(logging.DEBUG)
logger.debug("hi")

logger=logging.getLogger("pyin")
log=logger.debug

kbdbg_out = logging.StreamHandler(sys.stdout)
kbdbg_out.setLevel(logging.DEBUG)
kbdbg_out.setFormatter(logging.Formatter('%(message)s.'))
logger=logging.getLogger("kbdbg")
logger.addHandler(kbdbg_out)
kbdbg=logger.info
kbdbg("@prefix kbdbg: <http://kbd.bg/#> ")
kbdbg("@prefix : <file:///#> ")



def printify(iterable, separator):
	r = ""
	last = len(iterable) - 1
	for i, x in enumerate(iterable):
		r += str(x)
		if i != last:
			r += separator
	return r

class Triple():
	def __init__(s, pred, args):
		s.pred = pred
		s.args = args
	def __str__(s):
		return s.pred + "(" + printify(s.args, ", ") + ")"

class Graph(list):
	def __str__(s):
		return "{" + printify(s, ". ") + "}"

class Kbdbgable():
	last_instance_debug_id = 0
	def __init__(s):
		s.__class__.last_instance_debug_id += 1
		s.debug_id = s.__class__.last_instance_debug_id
		s.kbdbg_name = s.__class__.__name__ + str(s.debug_id)

class AtomVar(Kbdbgable):
	def __init__(s, debug_name, debug_locals):
		super().__init__()
		s.debug_name = debug_name
		s.debug_locals = weakref(debug_locals) if debug_locals != None else None
		if debug_locals != None:
			s.kbdbg_name = debug_locals.kbdbg_frame
		s.kbdbg_name += "_" + urllib.parse.quote_plus(debug_name)

class Atom(AtomVar):
	def __init__(s, value, debug_locals=None):
		super().__init__(value, debug_locals)
		s.value = value
	def __str__(s):
		return s.kbdbg_name + '("'+s.value+'")'

class Var(AtomVar):
	def __init__(s, debug_name, debug_locals=None):
		super().__init__(debug_name, debug_locals)
		s.bound_to = None
	def __str__(s):
		if s.bound_to:
			desc = '=' + str(s.bound_to)
		else:
			desc = '(free)'
		return s.kbdbg_name + desc
		# + " in " + str(s.debug_locals())

	def _bind_to(x, y):
		assert x.bound_to == None
		x.bound_to = y
		kbdbg(":"+x.kbdbg_name + " kbdbg:is_bound_to " + ":"+y.kbdbg_name)
		msg = "bound " + str(x) + " to " + str(y)
		log(msg)
		yield msg
		x.bound_to = None
		kbdbg(":"+x.kbdbg_name + " kbdbg:is_unbound_from " + ":"+y.kbdbg_name)

	def bind_to(x, y):
		for i in x._bind_to(y):
			yield i
		if type(y) == Var:
			log("and reverse?")
			for i in y._bind_to(x):
				yield i

class Locals(dict):
	def __init__(s, initializer, debug_rule, debug_id = 0, kbdbg_frame=None):
		super().__init__()
		s.debug_id = debug_id
		s.debug_last_instance_id = 0
		s.debug_rule = weakref(debug_rule)
		s.kbdbg_frame = kbdbg_frame
		for k,v in initializer.items():
			s[k] = v.__class__(v.debug_name, s)

	def __str__(s):
		r = ("locals " + str(s.debug_id) + " of " + str(s.debug_rule()))
		if len(s):
			r += ":\n#" + printify([str(k) + ": " + str(v) for k, v in s.items()], ", ")
		return r

	def new(s, kbdbg_frame):
		log("cloning " + str(s))
		s.debug_last_instance_id += 1
		r = Locals(s, s.debug_rule(), s.debug_last_instance_id, kbdbg_frame)
		log("result: " + str(r))
		return r

def tell_if_is_last_element(x):
	for i, j in enumerate(x):
		yield j, (i == (len(x) - 1))

class Rule(Kbdbgable):
	last_frame_id = 0
	def __init__(s, head, body=Graph()):
		super().__init__()
		s.head = head
		s.body = body
		s.locals_template = s.make_locals(head, body, s.kbdbg_name)
		s.ep_heads = []

		kbdbg(":"+s.kbdbg_name + ' a ' + 'kbdbg:rule')
		head = ":"+s.kbdbg_name + "Head"
		kbdbg(":"+s.kbdbg_name + ' kbdbg:has_head ' + head)

	def __str__(s):
		return "{" + str(s.head) + "} <= " + str(s.body)

	def make_locals(s, head, body, kbdbg_rule):
		locals = Locals({}, s)
		locals.kbdbg_frame = "locals_template_for_" + kbdbg_rule
		for triple in ([head] if head else []) + body:
			for a in triple.args:
				if is_var(a):
					x = Var(a, locals)
				else:
					x = Atom(a, locals)
				locals[a] = x
		return locals

	def unify(s, args):
		Rule.last_frame_id += 1
		frame_id = Rule.last_frame_id

		depth = 0
		generators = []
		max_depth = len(args) + len(s.body) - 1
		kbdbg_name = s.kbdbg_name + "Frame"+str(frame_id)
		locals = s.locals_template.new(kbdbg_name)
		def desc():
			return ("\n#vvv\n#" + str(s) + "\n" +
			"#args:" + str(args) + "\n" +
			"#locals:" + str(locals) + "\n" +
			"#depth:"+ str(depth) + "/" + str(max_depth)+
			        "\n#^^^")
		kbdbg(":"+kbdbg_name + " kbdbg:is_for_rule :rule" + str(s.debug_id))
		log ("entering " + desc())
		while True:
			if len(generators) <= depth:
				generator = None

				if depth < len(args):
					arg_index = depth
					head_thing = get_value(locals[s.head.args[arg_index]])
					generator = unify(get_value(args[arg_index]), head_thing)
				else:
					body_item_index = depth - len(args)
					triple = s.body[body_item_index]
					
					bi_args = []
					for i in triple.args:
						a = get_value(locals[i])
						bi_args.append(a)
					generator = pred(triple.pred, bi_args)
				generators.append(generator)
				log("generators:%s", generators)
		
			try:
				generators[depth].__next__()
				log ("back in " + desc() + "\n# from sub-rule")
				if (depth < max_depth):
					log ("down")
					depth+=1
				else:
					print ("#NYAN")
					yield locals#this is when it finishes a rule
					log ("re-entering " + desc() + " for more results")
			except StopIteration:
				if (depth > 0):
					log ("back")
					depth-=1
				else:
					log ("rule done")
					break#if it's tried all the possibilities for finishing a rule

	def find_ep(s, args):
		log ("ep check: %s vs..", args)
		for former_args in s.ep_heads:
			log(former_args)
			if ep_match(args, former_args):
				log("..hit")
				return True
		log ("..no match")

	def match(s, args=[]):
		s.ep_heads.append(args)
		for i in s.unify(args):
			s.ep_heads.pop()
			yield i
			s.ep_heads.append(args.copy())
		s.ep_heads.pop()

def ep_match(a, b):
	assert len(a) == len(b)
	for i, j in enumerate(a):
		if type(j) != type(b[i]):
			return
		if type(j) == str and b[i] != j:
			return
	return True

def asst(x):
	if type(x) == tuple:
		for i in x:
			asst(i)
	else:
		assert type(x) in [Var, Atom]

def unify(x, y):
	asst((x, y))
	log("unify " + str(x) + " with " + str(y))
	if type(x) == Var:
		return x.bind_to(y)
	elif type(y) == Var:
		return y.bind_to(x)
	elif x.value == y.value:
		msg = "equal consts:"+str(x)
		log(msg)
		return success(msg)
	else:
		return fail()

def fail():
	while False:
		yield

def success(msg):
	yield msg

def is_var(x):
	return x.startswith('?')

def get_value(x):
	asst(x)
	if type(x) == Atom:
		return x
	v = x.bound_to
	if v:
		return get_value(v)
	else:
		return x

def pred(p, args):
	for i in args:
		asst(i)
		assert get_value(i) == i
	for rule in preds[p]:
		if(rule.find_ep(args)): continue
		for i in rule.match(args):
			yield i


from collections import defaultdict

def query(input_rules, input_query):
	global preds
	preds = defaultdict(list)
	for r in input_rules:
		preds[r.head.pred].append(r)
	for nyan in Rule(None, input_query).match():
		yield nyan

	for nyan in Rule(None, Graph([Triple('a', ['socrates', 'mortal'])])).match():Autocompletion
		print ("#he's mortal, and he's dead")
	print ("#who is mortal?")
	#for nyan in pred('a', [v, 'mortal']):
	#v = Var('?who who')
	w = '?who'
	input_query = Graph([Triple('a', [w, 'mortal'])])
	for nyan in query(input_rules, input_query):
		print ('#'+str(nyan[w]) + " is mortal, and he's dead")


if __name__ == "__main__":
	test1()

