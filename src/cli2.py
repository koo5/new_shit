#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import nodes
nodes.autocomplete  = False

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

def parse(text):
	for i,x in enumerate(text):#this just prints the characters you got from stdin
		print(i, x)#prefixed by their position in the string
	m.enqueue_precomputation(None)
	return handle(text)

r = nodes.make_root()
scope = r['repl'].scope()
m.collect_grammar(scope,nodes.B.statement)

if __name__=='__main__':
	if len(sys.argv) == 3 and sys.argv[1] == '-c':
		text = sys.argv[2]
	elif len(sys.argv) == 2:
		text = open(sys.argv[1]).read()
	elif len(sys.argv) == 1:
		text = sys.stdin.read()[:-1]
	else: assert (false)
	print ("input:\n" + text)
	p=parse(text)[0]
	print (p.eval())
	#reads stdin, cuts off last char

