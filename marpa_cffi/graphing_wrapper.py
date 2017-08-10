"""
this replaces a few functions of marpa_cffi with wrappers that collect rules etc. usage:
import graphing_wrapper
graphing_wrapper.start()
optionally set:
graphing_wrapper.symid2name = m.symbol2name
then finally:
graphing_wrapper.generate_gv() #or _png or _bnf

i can recommend https://github.com/jrfonseca/xdot.py for viewing the .gv file

you can try rendering the bnf with https://metacpan.org/pod/GraphViz2::Marpa
if you manage to install it (with cpan), then something like:
perl ~/downloads/MarpaX-Grammar-GraphViz2-1.05/scripts/bnf2graph.pl -legend 1 -marpa ~/downloads/MarpaX-Grammar-GraphViz2-1.05/share/metag.bnf -o grammar.svg -user grammar.bnf
should work

default filename is "grammar.XXX"
graphing_wrapper.stop() # you can restore original functions

"""

import html

from .marpa_cffi import lib

class Orig(object):
	pass
orig = Orig()

def clear():
	global syms, rules, seqs
	syms = []
	rules= []
	seqs = []

def symid2name(id):
	return str(id)

def ruleid2name(id):
	return str(id)

def symbol_new(g):
	s = orig.symbol_new(g)
	syms.append(s)
	return s

def rule_new(g,lhs,rhs,length):
	r = orig.rule_new(g,lhs,rhs,length)
	rules.append((r, lhs, rhs))
	return r

def sequence_new(g,lhs,rhs,separator, min, flags ):
	s = orig.sequence_new(g,lhs,rhs,separator, min, flags)
	seqs.append((s, lhs, rhs, separator, min))
	return s

def stop():
	lib.marpa_g_symbol_new = orig.symbol_new
	lib.marpa_g_rule_new = orig.rule_new
	lib.marpa_g_sequence_new = orig.sequence_new

def start():
	orig.symbol_new = lib.marpa_g_symbol_new
	lib.marpa_g_symbol_new = symbol_new
	orig.rule_new = lib.marpa_g_rule_new
	lib.marpa_g_rule_new = rule_new
	orig.sequence_new = lib.marpa_g_sequence_new
	lib.marpa_g_sequence_new = sequence_new

	clear()

'''
def sss(sym):
	r = str(sym)
	try:
		name = symid2name(sym)
	except:
		name = None
	if name:
		r += "_" + esc(name)
	return r
'''
def sss(sym):
	return escape_symbol_name_for_readable_printing(symid2name(sym))
	return (str(sym) + '_' + esc(symid2name(sym))).replace('\\', '\\\\')

def escape_symbol_name_for_readable_printing(name):
	if name == "":
		return "<empty name>"
	r = ""
	all_spaces = True
	for i,ch in enumerate(name):
		if ch not in " _[]":
			all_spaces = False
		if (len(name) == i + 1) and (ch in [' ', '\n', '\t']):
			all_spaces = True
		if (ch != "\n") and (ch.isalnum() or (not all_spaces and ch.isprintable())):
			r+=ch
		else:
			r+="<"+str(ch.encode(encoding='utf-8'))+">"
	return r

def generate_bnf(filename='grammar.bnf'):
	f = open(filename, "w")

	for id, lhs, rhs in rules:
		f.write(sss(lhs) + "\n\t::= " + ' '.join([sss(i) for i in rhs]) + '\n')

	for id, lhs, rhs, sep, min in seqs:
		f.write(sss(lhs) +
		        "\n\t::=" +
				sss(rhs) +
		        ('*' if min == 0 else '+') +
				'\n')
				#todo:sep

	f.close()



def generate_png(graph):
	graph.format = 'png'
	graph.render()

def generate_gv_dot(graph):
	graph.save()

def generate(name):
	print ("generate graph:"+name)
	import graphviz

	graph = graphviz.Digraph(name)
	
	for sym in syms:
#		try:
		label = sss(sym)
		color = 'black'
#		except:
#			label = str(sym)
#			color = 'gray'

		#print ("s", sym, label)

		label = label.replace('\\', '\\\\')

		graph.node(str(sym), label,
	                          #style="filled",
	                          #fillcolor="green",
	                          fontcolor=color)
	for id, lhs, rhs in rules:
#		print ("r", id)
		#if len(rhs) > 1:
			#sub = graphviz.Digraph()
		for i in rhs:
			graph.edge(str(lhs), str(i))


	for id, lhs, rhs, sep, min in seqs:
		graph.edge(str(lhs), str(rhs))
	
	print ("done")
	return graph

def generate2(name):
	print ("generate graph with records:"+name)
	import graphviz
	graph = graphviz.Digraph(name)
	rs = rules + seqs
	for r in rs:
		id, lhs, rhs = r[0], r[1], r[2]
		print (str(lhs) + ":=" + str(rhs))
		is_seq = (len(r) == 5)
		ports = '<<TABLE><tr><td port="lhs">' + html.escape(sss(lhs)) + ":=</td>"
		if type(rhs) != list:
			rhs = [rhs]
		for port,sym in enumerate(rhs):
			for r in rs:
				id2, lhs2, rhs2 = r[0], r[1], r[2]
				if lhs2 == sym:
					graph.edge(str(id2)+":lhs", str(id)+":"+str(port))
			ports += '<td port="' + str(port) + '">' + html.escape(sss(sym)) + '</td>'
		graph.node(str(id),
		ports + "</tr></TABLE>>",
	                          #style="filled",
	                          #fillcolor="green",
	                          fontcolor='black')

	print ("done")
	return graph


clear()

