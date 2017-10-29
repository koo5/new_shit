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
if source != None:
	print('source:'+source)
	assert(source.startswith('file://'))#todo use https://github.com/YAmikep/datasource/tree/master/datasource
	text = open(source[7:]).read()
else:
	text = input.value(command, ti.Value, None)
print ("input:\n" + text)

#from IPython import embed;embed()

do_graph_grammar = input.value(command, ti.DebugOptionGenerateGrammarGraphPngOn)
#do_graph_grammar = True


from lemon_args import args

print("do_graph_grammar:",do_graph_grammar)
if do_graph_grammar:
	args.graph_grammar = True
	from lemon_args import args
	args.log_parsing = True

import nodes
nodes.autocomplete = False

from marpa_cffi.marpa_rpc_client import MarpaClient
m = MarpaClient(print, True)

def parse_sync(p, text=None):
	m.clear()
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
			raise Exception(msg.message)

r = nodes.make_root()
if text.startswith("unhide"):
	starts_with_unhide = True
	module = r['cli dummy empty module']
else:
	starts_with_unhide = False
	module = r['repl']

items = text.split('\n-----\n')
for idx,i in enumerate(items):
	p = nodes.Parser()
	module.ch.statements.add(p)
	if idx == 0 and starts_with_unhide:
		p._type = nodes.B.unhidenode
	p.add(nodes.Text(value = i))
	if i == "":
		continue
	rr = parse_sync(p, i)
	if (rr and len(rr)):
		for i in rr:
			print("parse result:",i.tostr() if isinstance(i, nodes.Element) else str(i))
		p.items = [rr[-1]]
	else:
		print ("no parse")
		exit()

#module.fix_parents()


