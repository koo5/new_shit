#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from cli import parse


def do(t):
	p = parse(t)
	#or,
	if (len(p) > 1):
		for i,r in enumerate(p):
			print (i, ":", r)
			print(r.tostr())
		print( "we couldnt prove that our grammar isnt ambiguous, but we can tell that your program is!")
	else:

		for i,r in enumerate(p):
			print (i, ":", r)
			print(r.tostr())
			r = r.unparen()
		
			#type-check it before evaluating:
			print("type check:",r.type_check().tostr())
			print("eval:",r.eval().tostr())

for t in [
#"(\\a.b) c",
#"(\\a.a) c",
#"(\\a.a) \\b.b",
#"(\\a.(a b))",
#"(\\a.(a b)) \\c.c",
#"(\\a.(\\b.(a b))) \\c.c"
#"(\\a.(a a)) (\\a.(a a))"
#"(\\x.(\\x.x)) y"

#"(\\x:bool.x) y"
#"(\\x:bool.x) true!"
#"(\\x:bool.x) 11"
#"(\\x:bool.(\\x:bool.x)) y"

#"(\\x:bool.(\\x:bool.x)) true!"

#"(\\x:int.x) 11"
#"(\\x:int.x) true!"
#"(\\x:bool.(\\x:bool.x)) 11"

#"(\\x:int->int.x) (\\x:int.x)"
#"(\\x:bool->bool.x) (\\x:int.x)"
#nice
#"(\\x:bool->(bool->bool).x) (\\x:bool.(\\y:bool.y))"
#"(((\\x:bool->(bool->bool).x) (\\x:bool.(\\y:bool.y))) true!) false!"
#"(((\\x:bool->(bool->bool).x) (\\x:bool.(\\y:bool.x))) true!) false!"


#cube
#   e-------f
#  /|      /|
# / |     / |
#a--|----b  |
#|  g----|--h
#| /     | /
#c-------d


"(\\t:*.(\\x:t.x))"


]:
	do(t)

	
