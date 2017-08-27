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

def value(g, subject=None, predicate=rdflib.term.URIRef(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#value'), object=None, default=None, any=False):
	return g.value(subject, predicate, object, default, any)

def process_input(step, lines):
	g = Graph()
	i = "\n".join(lines)
	#print("i:", i)
	g.parse(data=i, format='turtle')
	#now query g and generate one graphviz image
	gv("digraph frame"+str(step) + "{")

	for rule in g.subjects(RDF.type, kbdbg.rule):
		do_rule(rule)

	for binding in g.subjects(RDF.type, kbdbg.binding):
		if g.value(binding, kbdbg.was_unbound):
			continue
		source_thing = g.value(binding, kbdbg.has_source)
		target_thing = g.value(binding, kbdbg.has_target)
		#
		target_frame = g.value(binding, kbdbg.belongs_to_frame)
		#
		target_name = g.value(binding, kbdbg.has_name)
		for port in rules[g.value(source_frame, kbdbg.belongs_to_rule)].body_ports:
		gv(source_frame + ":" + [source_name] -> " + target_frame






	gv("}")


def do_rule(rule):
		log (rule+":")
		head = g.value(rule, kbdbg.has_head)
		body_items_list_name = g.value(rule, kbdbg.has_body)
		#from IPython import embed;embed()
		html = '<<html><table><tr><td>{'
		port_index = 0
		if head:
			do_pred(port_index, html, head)
		html += '}'
		if body_items_list_name:
			html += ' <= {'
			body_items_collection = Collection(g, body_items_list_name)
			for body_item in body_items_collection:
				do_pred(port_index, html, body_item)
			html += '}'
		html = '</tr></table></html>>'
		rule_html_labels[rule] = html
		#thing_to_port[rule][

def do_term(port_index, html, term):
	pred = g.value(term, kbdbg.has_pred)
	html += pred + '(</td>'
	arg_index = 0
	for arg, is_last in tell_if_is_last_element(Collection(g, g.value(term, kbdbg.has_args))):
		port_name = rule + 'port' + str(port_index)
		html += '<td port="' + port_name + '">' + arg + '</td>'
		port_index += 1
		if not is_last:
			html += '<td>, </td>'
	html += '<td>). '






if __name__ == '__main__':
	input_file = open("kbdbg.turtle")
	lines = []
	#while True:
	#	lines.append(input_file.readline())
	#	if input_file.
	process_input(0, input_file)
