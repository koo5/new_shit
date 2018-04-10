#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import lemon_utils.lemon_logging

from rdflib.namespace import Namespace

le = Namespace('http://koo5.github.com/lemon/api#')
ti = Namespace('http://koo5.github.com/lemon/api/textinput#')
from rdflib import RDF

from jsonrpc import JSONRPCResponseManager, dispatcher

import socketserver


@dispatcher.add_method
def foobar(**kwargs):
	return kwargs["foo"] + kwargs["bar"]


dispatcher["echo"] = lambda s: s
dispatcher["add"] = lambda a, b: a + b


class MyTCPHandler(socketserver.StreamRequestHandler):
	def handle(self):
		self.data = self.rfile.readline()
		print("{} wrote:".format(self.client_address[0]))
		response = handle_message(self.data)
		self.wfile.write(response.encode("utf-8"))

def handle_message(data):
	print(data)
	response = JSONRPCResponseManager.handle(data, dispatcher)
	return response.json

from lemon_args import args
#do_graph_grammar = input.value(command, ti.DebugOptionGenerateGrammarGraphPngOn)
do_graph_grammar = True
print("do_graph_grammar:", do_graph_grammar)
if do_graph_grammar:
	args.graph_grammar = True
	#from lemon_args import args
	args.log_parsing = True


import nodes
nodes.autocomplete = False
r = nodes.make_root()

from marpa_cffi.marpa_rpc_client import MarpaClient


def _parse_sync(p, text=None):
	m = MarpaClient(print, True)
	m.clear()
	m.collect_grammar(p.full_scope(), p.scope(), p.type)  # parsed_symbol)
	m.enqueue_precomputation(None)
	while True:
		msg = m.t.output.get()
		if msg.message == 'precomputed':
			ts = m.string2tokens(text)
			print("tokens", ts)
			m.enqueue_parsing([ts, text])
		elif msg.message == 'parsed':
			return msg.results
		else:
			raise Exception(msg.message)

@dispatcher.add_method
def parse(text):
	if text == "":
		return False
	module = r['repl']
	p = nodes.Parser()
	module.ch.statements.add(p)
	p.add(nodes.Text(value=text))
	rr = _parse_sync(p, text)
	result = {}
	results = []
	result["results"] = results
	if (rr and len(rr)):
		for i in rr:
			print("parse result:%s" % i)
			if isinstance(i, nodes.Element):
				print(" - %s" % i.tostr())
			results.append({"value":i.serialize()})
	return result


if __name__ == "__main__":

	#just for quicker debugging
	handle_message(' {"id": null, "jsonrpc": "2.0", "method":"parse", "params":["pri"]}')

	HOST, PORT = "localhost", 9999
	while True:
		try:
			server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
		except OSError:
			PORT += 1
			continue
		with server:
			print("listening on %s : %s" % (HOST, PORT))
			server.serve_forever()
			break
