#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
from weakref import ref as weakref
import rdflib
from rdflib import Graph
from rdflib.namespace import Namespace
from rdflib.namespace import RDF
kbdbg = Namespace('http://kbd.bg/#')

gv_handler = logging.StreamHandler(sys.stdout)
gv_handler.setLevel(logging.DEBUG)
gv_handler.setFormatter(logging.Formatter('%(message)s.'))
logger=logging.getLogger("kbdbg")
logger.addHandler(gv_handler)
gv=logger.info

logger=logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.debug("hi")
log=logger.debug

def value(subject=None, predicate=rdflib.term.URIRef(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#value'), object=None, default=None, any=False):
	return value(subject, predicate, object, default, any)

def process_input(step, lines):
	g = Graph()
	i = "\n".join(lines)
	#print("i:", i)
	g.parse(data=i, format='turtle')
	#now query g and generate one graphviz image
	gv("digraph frame"+str(step) + "{")

	for rule in g.subjects(RDF.type, kbdbg.rule):
		log (rule+":")
		head = g.value(rule, kbdbg.has_head)
		#from IPython import embed;embed()
		html = '<<html><table><tr><td>{'
		port = 0
		if head:
			pred = g.value(head, kbdbg.has_pred)
			html += pred + '(</td>'
			arg_index = 0
			for arg, is_last in tell_if_is_last_element(Collection(g, g.value(head, kbdbg.has_args))):
				#g.value(
				pn = s.kbdbg_name + 'port' + str(port)
				html += '<td port="' + pn + '">' + arg + '</td>'
				#kbdbg(":"+s.kbdbg_name + ' kbdbg:has_port ' + ":"+pn)
				#kbdbg(":"+pn + ' kbdbg:belongs_to_thing "' + arg + '"')
				port += 1
				if not is_last:
					html += '<td>, </td>'
			html += '<td>).'
			html += '} <= {'

		body = g.value(rule, kbdbg.has_body)
		#from IPython import embed;embed()
		port = 0
		if head:
			pred = g.value(head, kbdbg.has_pred)
			html += pred + '(</td>'
			arg_index = 0
			for arg, is_last in tell_if_is_last_element(Collection(g, g.value(head, kbdbg.has_args))):
				#g.value(
				pn = s.kbdbg_name + 'port' + str(port)
				html += '<td port="' + pn + '">' + arg + '</td>'
				#kbdbg(":"+s.kbdbg_name + ' kbdbg:has_port ' + ":"+pn)
				#kbdbg(":"+pn + ' kbdbg:belongs_to_thing "' + arg + '"')
				port += 1
				if not is_last:
					html += '<td>, </td>'
			html += '<td>).'
			html += '} <= {'

		html ++ '}</td></tr></html>>"'

		rule_html_labels[rule] = html
		#thing_to_port[rule][






	gv("}")


if __name__ == '__main__':
	input_file = open("kbdbg.turtle")
	lines = []
	#while True:
	#	lines.append(input_file.readline())
	#	if input_file.
	process_input(0, input_file)
