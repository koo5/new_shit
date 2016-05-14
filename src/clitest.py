#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from cli import lc1


def do(t):
	for i,r in enumerate(lc1(t)):
		print (i, ":", r)
		print(r.tostr())
		print("eval:",r.eval().tostr())

for t in [
#"(\\a.b) c",
#"(\\a.a) c",
#"(\\a.a) \\b.b",
#"(\\a.(a b))",
#"(\\a.(a b)) \\c.c",
#"(\\a.(\\b.(a b))) \\c.c"
"(\\a.(a a)) (\\a.(a a))"
]:
	do(t)

	
