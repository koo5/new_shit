"""Utilities for writing code that runs on Python 2 and 3"""
"most stuff deleted to preliminarily make it work in brython"
# Copyright (c) 2010-2014 Benjamin Peterson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#import functools
import operator
import sys
#import types

__author__ = "Benjamin Peterson <benjamin@python.org>"
__version__ = "1.7.3"


# Useful for very coarse version differentiation.
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


if PY3:
	_meth_func = "__func__"
	_meth_self = "__self__"

	_func_closure = "__closure__"
	_func_code = "__code__"
	_func_defaults = "__defaults__"
	_func_globals = "__globals__"
else:
	_meth_func = "im_func"
	_meth_self = "im_self"

	_func_closure = "func_closure"
	_func_code = "func_code"
	_func_defaults = "func_defaults"
	_func_globals = "func_globals"


try:
	advance_iterator = next
except NameError:
	def advance_iterator(it):
		return it.next()
next = advance_iterator


try:
	callable = callable
except NameError:
	def callable(obj):
		return any("__call__" in klass.__dict__ for klass in type(obj).__mro__)


get_method_function = operator.attrgetter(_meth_func)
get_method_self = operator.attrgetter(_meth_self)
get_function_closure = operator.attrgetter(_func_closure)
get_function_code = operator.attrgetter(_func_code)
get_function_defaults = operator.attrgetter(_func_defaults)
get_function_globals = operator.attrgetter(_func_globals)


if PY3:
	def iterkeys(d, **kw):
		return iter(d.keys(**kw))

	def itervalues(d, **kw):
		return iter(d.values(**kw))

	def iteritems(d, **kw):
		return iter(d.items(**kw))

	def iterlists(d, **kw):
		return iter(d.lists(**kw))
else:
	def iterkeys(d, **kw):
		return iter(d.iterkeys(**kw))

	def itervalues(d, **kw):
		return iter(d.itervalues(**kw))

	def iteritems(d, **kw):
		return iter(d.iteritems(**kw))

	def iterlists(d, **kw):
		return iter(d.iterlists(**kw))

"""
_add_doc(iterkeys, "Return an iterator over the keys of a dictionary.")
_add_doc(itervalues, "Return an iterator over the values of a dictionary.")
_add_doc(iteritems,
		 "Return an iterator over the (key, value) pairs of a dictionary.")
_add_doc(iterlists,
		 "Return an iterator over the (key, [values]) pairs of a dictionary.")
"""

if PY3:
	unichr = chr
	if sys.version_info[1] <= 1:
		def int2byte(i):
			return bytes((i,))
	else:
		# This is about 2x faster than the implementation above on 3.2+
		int2byte = operator.methodcaller("to_bytes", 1, "big")
	byte2int = operator.itemgetter(0)
	indexbytes = operator.getitem
	iterbytes = iter
	import io
	StringIO = io.StringIO
	BytesIO = io.BytesIO
else:
	unichr = unichr
	int2byte = chr
	def byte2int(bs):
		return ord(bs[0])
	def indexbytes(buf, i):
		return ord(buf[i])
	def iterbytes(buf):
		return (ord(byte) for byte in buf)
	import StringIO
	StringIO = BytesIO = StringIO.StringIO



if PY3:
	str_and_uni = (str)
	unicode = str
else:
	str_and_uni = (str, unicode)

