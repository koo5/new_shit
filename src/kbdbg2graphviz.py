#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from weakref import ref as weakref
import rdflib
from rdflib import Graph
import sys
import logging

input_file = open("kbdbg.nt")
lines = []
while True:
	lines += input_file.readline()

def process_input(lines):
	g = Graph()
	g.parse("\n".join(lines), 'nt')
	#now query g and generate one graphviz image
	print(g.subject_objects('has_graphviz_html_label'))

