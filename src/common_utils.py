import sys
import rdflib
from rdflib import Graph

from rdflib.namespace import Namespace
le = Namespace('http://koo5.github.com/lemon/api#')
ti = Namespace('http://koo5.github.com/lemon/api/textinput#')
from rdflib import RDF



def parse_input():
	input_graph = Graph()

	print ("sys.argv: ",(sys.argv))
	if len(sys.argv) == 1 or sys.argv[1] == "-":
		print ('reading rdf from stdin until "fin."')
		input_lines = []
		for l in sys.stdin.readlines():
			print('line:' + l)
			if l == "fin.":
				break
			input_lines.append(l)
		input_graph.parse("\n".join(input_lines), 'nt')
	elif len(sys.argv) == 3 and sys.argv[1] == "--n3":
		print("rdf input on command line")
		input_graph.parse(data=sys.argv[2], format='n3')
	elif len(sys.argv) == 3 and sys.argv[1] == "--text":
		print("text input on command line")
		input_graph.add(( rdflib.term.URIRef('command'), RDF.type, le.TextInput))
		input_graph.add(( rdflib.term.URIRef('command'), ti.Value, rdflib.term.Literal(sys.argv[2])))
	elif len(sys.argv) == 3 and sys.argv[1] == "--txt":
		print("text input on command line")
		input_graph.add(( rdflib.term.URIRef('command'), RDF.type, le.TextInput))
		input_graph.add(( rdflib.term.URIRef('command'), ti.Source, rdflib.term.Literal('file://'+sys.argv[2])))
	elif len(sys.argv) == 2:
		fn = sys.argv[1]
		format = rdflib.util.guess_format(fn)
		print('format:' + str(format))
		if not format:
			raise Exception("input text format not recognized")
		input_graph.parse(fn, format=format)
	else:
		assert(False)
	return input_graph

