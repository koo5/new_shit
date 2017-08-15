#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import attr
from weakref import ref as weakref
import rdflib
from rdflib import Graph
import sys
import common_utils
#g = common_utils.parse_input()

from structlog import get_logger
sog = get_logger()
sog.info("hi", how="areyou")

import logging
formatter = logging.Formatter('#%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_debug_out = logging.StreamHandler()
console_debug_out.setFormatter(formatter)

kbdbg_out = logging.StreamHandler()
kbdbg_out.setLevel(logging.DEBUG)

logger=logging.getLogger()
logger.addHandler(console_debug_out)
logger.setLevel(logging.DEBUG)
logger.debug("hi")

logger=logging.getLogger("pyin")
log=logger.debug

logger=logging.getLogger("kbdbg")
logger.addHandler(kbdbg_out)
kbdbg=logger.info
kbdbg("this is sparta.")



def printify(iterable, separator):
	r = ""
	last = len(iterable) - 1
	for i, x in enumerate(iterable):
		r += str(x)
		if i != last:
			r += separator
	return r

@attr.s
class Kbdbgable(object):
	last_instance_debug_id = 0
	debug_id = attr.ib(init=False)
	@debug_id.default
	def _(s):
		s.__class__.last_instance_debug_id += 1
		return s.__class__.last_instance_debug_id
	kbdbg_name = attr.ib(init=False)
	@kbdbg_name.default
	def _(s):
		return s.__class__.__name__ + str(s.debug_id)

class Triple(object):
	def __init__(s, pred, args):
		s.pred = pred
		s.args = args

	def __str__(s):
		return s.pred + "(" + printify(s.args, ", ") + ")"

class Graph(list):
	def __str__(s):
		return "{" + printify(s, ". ") + "}"

class Locals(dict):
	def __init__(s, initializer, debug_rule, debug_id = 0):
		super().__init__(initializer)
		s.debug_id = debug_id
		s.debug_last_instance_id = 0
		s.debug_rule = weakref(debug_rule)

	def __str__(s):
		r = ("locals " + str(s.debug_id) + " of " + str(s.debug_rule()))
		if len(s):
			r += ":\n#" + printify([str(k) + ": " + str(v) for k, v in s.items()], ", ")
		return r

	def new(s):
		s.debug_last_instance_id += 1
		r = Locals(s, s.debug_rule(), s.debug_last_instance_id)
		return r

def tell_if_is_last_element(x):
	for i, j in enumerate(x):
		yield j, (i == (len(x) - 1))

class Rule(object):
	debug_id = 0
	def __init__(s, head, body=Graph()):
		Rule.debug_id += 1
		s.debug_id = Rule.debug_id
		s.head = head
		s.body = body
		s.locals_template = s.make_locals(head, body)
		s.ep_heads = []
		s.kbdbg_name = "rule" + str(s.debug_id)
		port = 0

		html = s.kbdbg_name + ' has_graphviz_html_label "<<html><table><tr><td>{'
		if head:
			html += head.pred + '(</td>'
			for arg, is_last in tell_if_is_last_element(head.args):
				html += '<td port="' + str(port) + '">' + arg + '</td>'
				pn = s.kbdbg_name + 'port' + str(port)
				kbdbg(s.kbdbg_name + ' has_port ' + pn + '.')
				kbdbg(pn + ' belongs_to_thing "' + arg + '".')
				port += 1
				if not is_last:
					html += '<td>, </td>'
			html += '<td>).'
		html += '} <= {'
		kbdbg(html + '}</td></tr></html>>".')

	def __str__(s):
		return "{" + str(s.head) + "} <= " + str(s.body)

	def make_locals(s, head, body):
		locals = Locals({}, s)
		for triple in ([head] if head else []) + body:
			for a in triple.args:
				if is_var(a):
					x = Var(a, locals)
				else:
					x = Atom(a, locals)
				locals[a] = x
		return locals

	def unify(s, args):
		depth = 0
		generators = []
		max_depth = len(args) + len(s.body) - 1
		locals = s.locals_template.new()
		def desc():
			return ("\n#vvv\n#" + str(s) + "\n" +
			"#args:" + str(args) + "\n" +
			"#locals:" + str(locals) + "\n" +
			"#depth:"+ str(depth) + "/" + str(max_depth)+
			        "\n#^^^")
		log ("entering " + desc())
		kbdbg_name = s.kbdbg_name + "frame"+str(locals.debug_id)
		kbdbg(kbdbg_name + " :is_for_rule rule" + str(s.debug_id))
		while True:
			if len(generators) <= depth:
				generator = None

				if depth < len(args):
					arg_index = depth
					head_thing = s.head.args[arg_index]
					if is_var(head_thing):
						head_thing = get_value(locals[head_thing])
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
					yield "NYAN"#this is when it finishes a rule
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
			yield "nyan"
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

@attr.s
class Atom(Kbdbgable):
	value = attr.ib()
	debug_locals = attr.ib(convert=weakref)


@attr.s
class Var(Kbdbgable):
	debug_name = attr.ib(default="unnamed")
	debug_locals = attr.ib(convert=weakref, default=None)
	bound_to = attr.ib(default=None, init=False)
	@property
	def kbdbg_name(s):
		return super().kbdbg_name+"_"+s.debug_name
	def __str__(s):
		if s.bound_to:
			desc = '=' + str(s.bound_to)
		else:
			desc = '(free)'
		return s.debug_name + desc
		# + " in " + str(s.debug_locals())
	def bind_to(x, y):
		assert x.bound_to == None
		x.bound_to = y
		kbdbg(x.kbdbg_name + " is_bound_to " + y.kbdbg_name)
		msg = "bound " + str(x) + " to " + str(y)
		log(msg)
		yield msg
		x.bound_to = None
		kbdbg(x.kbdbg_name + " is_unbound_from " + y.kbdbg_name)
		if type(y) == Var:
			sog("and reverse?")
			for i in y.bind_to(x):
				yield i


def unify(x, y):
	log("unify " + str(x) + " with " + str(y))
	if x == y:
		assert type(x) == str
		msg = "equal consts:"+x
		log(msg)
		return success(msg)
	if type(x) == Var:
		return x.bind_to(y)
	elif type(y) == Var:
		return y.bind_to(x)
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
	if type(x) == Atom:
		return x
	v = x.bound_to
	if v:
		return get_value(v)
	else:
		return x

def pred(p, args):
	for i in args:
		assert get_value(i) == i
	for rule in preds[p]:
		if(rule.find_ep(args)): continue
		for i in rule.match(args):
			yield "nyan"


from collections import defaultdict

if __name__ == "__main__":
	preds = defaultdict(list)

	for r in [
	Rule(Triple('a', ['?X', 'mortal']), Graph([Triple('a', ['?X', 'man']), Triple('not', ['?X', 'superman'])])),
	Rule(Triple('a', ['socrates', 'man'])),
	Rule(Triple('a', ['koo', 'man'])),
	Rule(Triple('not', ['?nobody', 'superman']))]:
		preds[r.head.pred].append(r)

	for nyan in Rule(None, Graph([Triple('a', ['socrates', 'mortal'])])).match():
		print (nyan)
		print ("he's mortal, and he's dead")

	print ("who is mortal?")
	v = Var('?who who')
#	for nyan in pred('a', [v, 'mortal']):
#		print (str(v) + " is mortal, and he's dead")
