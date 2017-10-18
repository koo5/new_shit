
def flatten_gen(kc, x):
	
	#kc stands for "kill counter" and is supposed to decrement in each nesting
	print ("kc:"+str(kc))
	if kc == 0:
		yield "killoff"
		return
	
	for y in x:
		print (y)
		if not isinstance(y, list):
			print ("yielding y "+str(y))
			yield y
		else:
			for z in flatten_gen(kc-1, y):
				print ("yielding z "+str(z))
				yield z

i = [3,[4,5],[[6,[7],8]]]
o = list(flatten_gen(3, i))
assert o == [3,4,5,6,7,8], o
print(o)

