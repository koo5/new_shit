import pyswip
prolog = pyswip.Prolog()
prolog.consult("wat.pl")
works_ass = pyswip.Functor("works_ass", 2)
X = pyswip.Variable()
q = pyswip.Query(works_ass(X, 'statement'))
while q.nextSolution():
	v = str(X.value)
	print v
q.closeQuery()
