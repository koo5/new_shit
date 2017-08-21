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

def process_input(step, lines):
	g = Graph()
	i = "\n".join(lines)
	#print("i:", i)
	g.parse(data=i, format='turtle')
	#now query g and generate one graphviz image
	gv("digraph frame"+str(step) + "{")

	for x in g.subjects(RDF.type, kbdbg.rule):
		print (x)


	for rule, head in g.subjects(kbdbg.has_head):
		#from IPython import embed;embed()
		label = '<<html><table><tr><td>{'
		port = 0
		if head:
			html += head.pred + '(</td>'
			for arg, is_last in tell_if_is_last_element(head.args):
				pn = s.kbdbg_name + 'port' + str(port)
				html += '<td port="' + pn + '">' + arg + '</td>'
				kbdbg(":"+s.kbdbg_name + ' kbdbg:has_port ' + ":"+pn)
				kbdbg(":"+pn + ' kbdbg:belongs_to_thing "' + arg + '"')
				port += 1
				if not is_last:
					html += '<td>, </td>'
			html += '<td>).'
			html += '} <= {'
			kbdbg(html + '}</td></tr></html>>"')

		labels[rule] = label

	gv("digraph frame"+str(step) + "}")


if __name__ == '__main__':
	input_file = open("kbdbg.turtle")
	lines = []
	#while True:
	#	lines.append(input_file.readline())
	#	if input_file.
	process_input(0, input_file)
