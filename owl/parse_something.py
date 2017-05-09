#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from lemon_utils.lemon_six import iteritems
from lemon_utils.utils import Evil
import lemon_utils.lemon_logging
import logging
logger=logging.getLogger("root")
log=logger.debug
info=logger.info


import lemon_args2


lemon_args2.parse_args()
from lemon_args2 import args


import os
import surf
store = surf.Store(reader = "rdflib",writer = "rdflib",rdflib_store = "IOMemory")
store.load_triples(source = (os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '.')
+"/lemon.owl")
lemon = surf.namespace.Namespace("http://www.semanticweb.org/kook/ontologies/2017/3/lemon#")
session = surf.Session(store)
Compound = session.get_class(lemon.Compound)
#Parser = session.get_class(lemon.Parser)
#parser = Parser()
#parser.text = "hello"
#parser.scope = \
print session.get_resource(lemon.BuiltinsStatementsItems)


import IPython; IPython.embed()






def collect_grammar(scope,  start=None):
		"""scope: a list of modules or nodes"""
		assert scope == uniq(scope)
		s.clear()
		s.scope = scope

		#tokenization stuff:
		#any char used in any terminal of the grammar:
		s.named_symbol('known_char')
		#all the rest:
		s.named_symbol('nonspecial_char')
		#maybe just convenience
		s.named_symbol('maybe_spaces')
		s.sequence('maybe_spaces', s.syms.maybe_spaces, s.known_char(' '), action=ignore, min=0)

		#anything means we are parsing for the editor and want to parse any fragments of the language
		anything = start==None
		if anything:
			s.start=s.named_symbol('start')
		else:
			s.start = start.symbol # for example mltt expression
		log("start=", s.start )

		for i in scope:
			if isinstance(i, SyntacticCategory):
				i._symbol = m.symbol(s.name)
				continue
			elif isinstance(i, WorksAs):
				if i._rule != None:
					continue
				lhs = i.ch.sup.parsed
				rhs = i.ch.sub.parsed
				if not isinstance(lhs, Ref) or not isinstance(rhs, Ref):
					print ("invalid sub or sup in worksas")
					continue
				lhs = lhs.target.symbol
				rhs = rhs.target.symbol
				if args.log_parsing:
					log('%s %s %s %s %s'%(i, i.ch.sup, i.ch.sub, lhs, rhs))
				if lhs != None and rhs != None:
					r = m.rule(str(i), lhs, rhs)
					i._rule = r
			else:
				#the property is accessed, forcing registering of the grammar
				_ = i.symbol

		if anything:
			for i in scope:
				if i.symbol != None:
					if args.log_parsing:
						log(i.symbol)
						rulename = 'start is %s' % s.symbol2debug_name(i.symbol)
					else:
						rulename = ""
					s.rule(rulename , s.start, i.symbol)

		"""
		sups = DefaultDict(list)
		pris = DefaultDict(list)
		asoc = DefaultDict(-1)

		for n in scope:
			if n.__class__.__name__ == 'WorksAs':
				sups[n.ch.sup.parsed.target.symbol].append(n.ch.sub.parsed.target.symbol)
			if n.__class__.__name__ == 'HasPriority':
				pris[n.ch.value.parsed.pyval].append(n.ch.node.parsed.target.symbol)
			if n.__class__.__name__ == 'HasAssociativity':
				asoc[n.ch.value.parsed.pyval].append(n.ch.node.parsed.target.symbol)

		this is some nonsense
		for k,v in sups:
			for sub in v:
				???pri = pris[sub]
				if not pri in level_syms[sup]:
					level_syms[sup][pri] = s.symbol(sup.name + pri)
				lhs = level_syms[sup][pri]
				rhs =
				pris[sub]

		"""







exit()










def enqueue_precomputation(s, for_node):
	s.t.input.put(Dotdict(
			task = 'feed',
			num_syms = s.num_syms,
			symbol_ranks = s.symbol_ranks,
			rules = s.rules[:],
			for_node = for_node,
			start=s.start))

	def enqueue_parsing(s, tr):
		s.t.input.put(Dotdict(
			task = 'parse',
			tokens = tr[0],
			raw = tr[1],
			rules = s.rules[:]))


def precompute():
	r = Request()
	r.work = 'precompute'
	#r.node =

def on_rpc_message(s,m):
	if m.message == 'precomputed':

			#if m.for_node == s.current_parser_node:
				node = m.for_node()
				if node:#brainfart
					s.marpa.enqueue_parsing(s.parser_items2tokens(node))
	elif m.message == 'parsed':
				log (m.results)
				s.parse_results = [nodes.ParserMenuItem(['a parse'], x) for x in m.results]
				s.update_items()
				#	r.append(ParserMenuItem(i, 333))
				s.signal_change()



#for x in list_items(builtins.hasItems):

def parsed():
	if isinstance(Parser):
		text = parser.text

"""
surf + rdf
ordf + owl
prolog +








"""


















