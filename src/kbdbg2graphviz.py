#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from weakref import ref as weakref
import rdflib
from rdflib import Graph
import sys
import logging
from rdflib.namespace import Namespace
kbdbg = Namespace('http://kbd.bg/#')


def process_input(lines):
	g = Graph()
	i = "\n".join(lines)
	print("i:", i)
	g.parse(data=i, format='turtle')
	#now query g and generate one graphviz image
	print(g.subject_objects(kbdbg.has_head))

	"""
			#kbdbg:has_graphviz_html_label "<<html><table><tr><td>{'
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
	"""


if __name__ == '__main__':
	input_file = open("kbdbg.turtle")
	lines = []
	while True:
		lines.append(input_file.readline())
		process_input(lines)
