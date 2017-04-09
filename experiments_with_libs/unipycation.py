# region unipycation
"""

#import uni


def ph_to_lemon(x):
	return iter([to_lemon(x)])


if __name__ == "__main__":
	print "testing.."
	e = uni.Engine("""

"""

do(1, A) :-
	python:to_lemon(3, A).
%	python:print(A).

"""
""", globals())

	print [x for x in e.db.do.iter(1, None)]
"""

# endregion
