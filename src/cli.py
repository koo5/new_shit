#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys



import lemon_utils.lemon_logging
import marpa_cffi.graphing_wrapper as graphing_wrapper
from marpa_cffi.marpa_cffi import lib
lib.rule_new = graphing_wrapper.rule_new
graphing_wrapper.start()


import nodes

from marpa_cffi.marpa_rpc_client import ThreadedMarpa
nodes.m = m = ThreadedMarpa(print, True)


graphing_wrapper.symid2name = m.symbol2debug_name



def handle(text=None):
	msg = m.t.output.get()
	if msg.message == 'precomputed':
		ts = m.string2tokens(text)
		print ("tokens", ts)
		m.enqueue_parsing([ts, text])
		

		graphing_wrapper.generate_png()
		graphing_wrapper.generate_gv()
		
		
		return handle()
	elif msg.message == 'parsed':
		print (len(msg.results), "results")
		return msg.results

def parse(text):
	#this just prints the characters you got from stdin
	#prefixed by their position in the string
	for i,x in enumerate(text):
		print(i, x)
	m.enqueue_precomputation(None)
	return handle(text)


mod="lc1-test",nodes.lc1
mod="lc2-test",nodes.lc2



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

