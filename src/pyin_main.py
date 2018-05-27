#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rdflib

from pyin import *

import click

@click.command()
@click.argument('kb', type=click.File('rb'))
@click.argument('goal', type=click.File('rb'))
def query_from_files(kb, goal):
	default_graph = '@default'
	implies = URIRef("http://www.w3.org/2000/10/swap/log#implies")

	graph = rdflib.ConjunctiveGraph(identifier=default_graph)
	graph.parse(kb, format='nquads')

	rules = []

	for s,p,o in graph.triples((None, None, None, default_graph)):
		if p != implies:
			rules.append(Rule(Triple((p), [(s), (o)]), Graph()))
		else:
			for head_triple in graph.get_context(o):
				#print()
				#print(head_triple, "<=")
				body = Graph()
				for body_triple in graph.get_context(s):
					#print(body_triple)
					body.append(Triple((body_triple[1]), [(body_triple[0]), (body_triple[2])]))
				rules.append(Rule(Triple((head_triple[1]), [(head_triple[0]), (head_triple[2])]), body))

	graph = rdflib.Graph()
	graph.parse(goal, format='nquads')

	goal = Graph()
	for s,p,o in graph.triples((None, None, None)):
		goal.append(Triple((p), [(s), (o)]))

	def substitute(node, locals, is_pred_string = False):
		if node in locals:
			v = get_value(locals[node])
			if type(v) == Var:
				return node
			elif type(v) == Atom:
				return v.value
			else:
				666
		return node

	for i in query(rules, goal):
		o = ' RESULT : '
		for triple in goal:
			#from IPython import embed; embed()
			#n1 = substitute(triple.args[0], i)
			#from IPython import embed; embed()
			o += substitute(triple.args[0], i).n3() + " " + substitute((triple.pred), i).n3() + " " + substitute(triple.args[1], i).n3() + "."
			print(o)
		print (i.__short__str__())
		print ()



if __name__ == "__main__":
	query_from_files()
