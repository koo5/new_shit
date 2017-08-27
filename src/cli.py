#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import lemon_utils.lemon_logging
from marpa_cffi.marpa_cffi import lib

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

	
#mod="lc1-test",nodes.lc1
#mod="lc2-test",nodes.lc2
#mod="cube-test",nodes.cube
mod="MLTT-test",nodes.MLTT


#so this runs before the __main__ is called
r = nodes.make_root()
scope = r[mod[0]].scope()
m.collect_grammar(scope,mod[1].exp)

#the condition is true when you do like python ./cli.py,
#false when you run ipython and just import cli
if __name__=='__main__':
	text = sys.stdin.read()[:-1]
	p=parse(text)[0]
	print (p.eval())
	#reads stdin, cuts off last char

