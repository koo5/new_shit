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
		for i,r in enumerate(msg.results):
			print (i, ":", r)
			print("\n")
		return msg.results

def lc1(text):

	for i,x in enumerate(text):
		print(i, x)
	m.enqueue_precomputation(None)
	return handle(text)

r = nodes.make_root()
scope = r["lc1-test"].scope()
m.collect_grammar(scope)


if __name__=='__main__':
	text = sys.stdin.read()[:-1]
	lc1(text)

