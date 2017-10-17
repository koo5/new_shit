#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import lemon_utils.lemon_logging



import common_utils
input = common_utils.parse_input()

from rdflib.namespace import Namespace
le = Namespace('http://koo5.github.com/lemon/api#')
ti = Namespace('http://koo5.github.com/lemon/api/textinput#')
from rdflib import RDF
command = input.value(None, RDF.type, le.TextInput)
source = input.value(command, ti.Source, None)
print('source:'+source)
assert(source.startswith('file://'))#todo use https://github.com/YAmikep/datasource/tree/master/datasource
text = open(source[7:]).read()
print ("input:\n" + text)

#from IPython import embed;embed()

from lemon_args import args
do_graph_grammar = input.value(command, ti.DebugOptionGenerateGrammarGraphPngOn)
print("do_graph_grammar:",do_graph_grammar)
if do_graph_grammar:
	args.graph_grammar = True
	from lemon_args import args
	args.log_parsing = True

import nodes
nodes.autocomplete = False

from marpa_cffi.marpa_rpc_client import ThreadedMarpa
nodes.m = m = ThreadedMarpa(print, True)

def parse_sync(p, text=None):
	m.collect_grammar(p.full_scope(), p.scope(), p.type)#parsed_symbol)
	m.enqueue_precomputation(None)
	while True:
		msg = m.t.output.get()
		if msg.message == 'precomputed':
			ts = m.string2tokens(text)
			print ("tokens", ts)
			m.enqueue_parsing([ts, text])
			#recurse to wait for 'parsed'
		elif msg.message == 'parsed':
			return msg.results
		else:
			raise 666

r = nodes.make_root()
module = r['cli dummy empty module']
p = nodes.Parser()
module.ch.statements.add(p)
if text.startswith("unhide"):
	p._type = nodes.B.unhidenode
	split = text.index("\n")
	first_line = text[:split]
	rest_of_lines = text[split:]
	p.add(nodes.Text(value = text))
	r = parse_sync(p, first_line)
	if (r and len(r)):
		p=r[0]
		print (p.eval())
	p = nodes.Parser()
	module.ch.statements.add(p)
	p.add(nodes.Text(value=rest_of_lines))

else:
	print ("no parse")

