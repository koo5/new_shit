#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import lemon_utils.lemon_logging


import nodes
from marpa_cffi.marpa_rpc_client import ThreadedMarpa



nodes.m = m = ThreadedMarpa(print, True)


def handle():
	msg = m.t.output.get()
	if msg.message == 'precomputed':
		ts = m.string2tokens(text)
		print ("tokens", ts)
		m.enqueue_parsing([ts, text])
		handle()
	elif msg.message == 'parsed':
		print (len(msg.results), "results")
		for i,r in enumerate(msg.results):
			print (i, ":", r)
			print("\n")


text = sys.stdin.read()
r = nodes.make_root()
scope = r["lc1-test"].scope()
m.collect_grammar(scope)
m.enqueue_precomputation(None)
handle()

