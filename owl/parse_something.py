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



import surf

lemon = surf.namespace.Namespace("http://www.semanticweb.org/kook/ontologies/2017/3/untitled-ontology-16")



store = surf.Store(reader = "rdflib",writer = "rdflib",rdflib_store = "IOMemory")
session = surf.Session(store)


store.load_triples(source = "lemon.owl")
Compound = session.get_class(lemon.Compound)

import IPython; IPython.embed()

parser = Compound()
parser.

#Compound.get_resource(


all_persons = Person.all()

print "Found %d persons in Tim Berners-Lee's FOAF document" % (len(all_persons))

for person in all_persons:
	print person.foaf_name.first
