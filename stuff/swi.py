import weakref
from pyswip import *

#ok  so another hassle with pyswip is that swi-prolog in ubuntu ships
#compiled without shared lib. bummer.


#http://stackoverflow.com/questions/12428026/safely-iterating-over-weakkeydictionary-and-weakvaluedictionary

py2pl = weakref.WeakKeyDictionary()
pl2py = weakref.WeakValueDictionary()

c = 0

def to_pl(pyobj):
	global c
	if not py2pl.has_key(pyobj):
		name = "py"+str(c)
		py2pl[pyobj] = Atom(name)
		pl2py[name] = pyobj
		c += 1
	return py2pl[pyobj]

prolog = pyswip.Prolog()
prolog.consult("wat.pl")
pl_works_as_nodes = pyswip.Functor("works_as_nodes", 2)

def works_as(y):
	y = to_swi(y)
	r = []
	X = pyswip.Variable()
	q = pyswip.Query(pl_works_as_nodes(X, y))
	while q.nextSolution():
		r += [str(X.chars)]
	q.closeQuery()
	#print r
	return r


def node_works_as(*a):
	a[0]

registerForeign(node_works_as, arity=2)





"""
#nodes.pyswip.prolog._original_sys_exit
#+prolog.consult("wat.pl")
+node_works_as = pyswip.Functor("node_works_as", 2)
+
+               X = pyswip.Variable()
+               for t in self.types:
+                       q = pyswip.Query(node_works_as(X, t))
+                       while q.nextSolution():
+                               v = str(X.value)
+                               print v
+                               r += [it(protos[v])]
+               q.closeQuery()
+
"""
