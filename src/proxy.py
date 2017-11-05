import weakref

proxy = weakref.WeakKeyDictionary()
reverse = weakref.WeakValueDictionary()

counter = 0

def make_proxy(x):
	#print("make_proxy:", x)
	try:
		return proxy[x]
	except KeyError:
		global counter
		counter += 1
		proxy[x] = counter
		reverse[counter] = x
		return counter

def reverse_proxy(num):
	return reverse[num]