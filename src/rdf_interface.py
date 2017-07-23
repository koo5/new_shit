#!/usr/bin/env ipython3
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

#from IPython import embed;embed()

from lemon_args import args
do_graph_grammar = input.value(command, ti.DebugOptionGenerateGrammarGraphPngOn)
print("do_graph_grammar:",do_graph_grammar)
if do_graph_grammar:
	args.graph_grammar = True

import nodes
nodes.autocomplete = False

from marpa_cffi.marpa_rpc_client import ThreadedMarpa
nodes.m = m = ThreadedMarpa(print, True)

def handle(text=None):
	msg = m.t.output.get()
	if msg.message == 'precomputed':
		ts = m.string2tokens(text)
		print ("tokens", ts)
		m.enqueue_parsing([ts, text])
		#recurse to wait for 'parsed'
		return handle()
	elif msg.message == 'parsed':
		print (len(msg.results), "results")
		return msg.results
	else:
		print(msg)

def parse(text):
	for i,x in enumerate(text):#this just prints the characters you got from stdin
		print(i, x)#prefixed by their position in the string
	m.enqueue_precomputation(None)
	return handle(text)

r = nodes.make_root()
scope = r['repl'].scope()
m.collect_grammar(scope,nodes.B.statement)

print ("input:\n" + text)
p=parse(text)[0]
print (p.eval())
