

import sys

_pyversion = sys.version_info[0]

def callback_method(func):
	def notify(self,*args,**kwargs):
		for _,callback in self._callbacks:
			callback()
		return func(self,*args,**kwargs)
	return notify

class NotifyingList(list):
	"#http://stackoverflow.com/a/13259435/376258"

	extend = callback_method(list.extend)
	append = callback_method(list.append)
	remove = callback_method(list.remove)
	pop = callback_method(list.pop)
	__delitem__ = callback_method(list.__delitem__)
	__setitem__ = callback_method(list.__setitem__)
	__iadd__ = callback_method(list.__iadd__)
	__imul__ = callback_method(list.__imul__)

	if _pyversion < 3:
		__setslice__ = callback_method(list.__setslice__)
		__delslice__ = callback_method(list.__delslice__)

		def __getslice__(self,*args):
			if self._slicing_creates_notifyinglist:
				return self.__class__(list.__getslice__(self,*args))
			else:
				return list.__getslice__(self,*args)

	def __getitem__(self,item):
		if self._slicing_creates_notifyinglist and isinstance(item,slice):
			return self.__class__(list.__getitem__(self,item))
		else:
			return list.__getitem__(self,item)

	def __init__(self, iterable=[], slicing_creates_notifyinglist=False):
		list.__init__(self, iterable)
		self._callbacks = [] #i dont need multiple callbacks and why the counter, but ok
		self._callback_cntr = 0
		self._slicing_creates_notifyinglist = slicing_creates_notifyinglist

	def register_callback(self,cb):
		self._callbacks.append((self._callback_cntr,cb))
		self._callback_cntr += 1
		return self._callback_cntr - 1

	def unregister_callback(self,cbid):
		for idx,(i,cb) in enumerate(self._callbacks):
			if i == cbid:
				self._callbacks.pop(idx)
				return cb
		else:
			return None


if __name__ == '__main__':
	A = NotifyList(range(10), True)
	def cb():
		print ("Modify!")

	#register a callback
	cbid = A.register_callback(cb)

	A.append('Foo')
	A += [1,2,3]
	A *= 3
	A[1:2] = [5]
	del A[1:2]

	#Add another callback.  They'll be called in order (oldest first)
	def cb2():
		print ("Modify2")
	A.register_callback(cb2)
	print ("-"*80)
	A[5] = 'baz'
	print ("-"*80)

	#unregister the first callback
	A.unregister_callback(cbid)

	A[5] = 'qux'
	print ("-"*80)

	print (A)
	print (type(A[1:3]))
	print (type(A[1:3:2]))
	print (type(A[5]))