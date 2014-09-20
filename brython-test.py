from weakref import ref as weakref
a = weakref(object)
print (a)
b = a.obj.obj
print (b)
assert b == object

