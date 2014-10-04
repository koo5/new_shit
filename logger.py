from __future__ import unicode_literals
from __future__ import print_function
import traceback, logging
from inspect import *

#logging is really only for debugging purposes. users will have key/action log frame.

#stickittothemain: todo: lets do the verbosity level thing or rather topics? and argument --log-events?

#https://code.google.com/p/kosciak-misc/source/browse/python/examples/curses/CursesHandler.py?spec=svn145&r=34

debug = print

#gui = None

topics = ["?"]

def topic(text=None):
	"""decorator to put before your function with a logging topic"""
	if text == None:
		text = function_with_decorator.__name__ #todo: add class

	def decorator_inner_crap(function_with_decorator):
		def wrapped_function(*vargs, **kwargs):
			topics.append(text)
			result = function_with_decorator(*vargs, **kwargs)
			topics.pop()
			return result
		#copy useful attributes of the wrapped function to the wrapper
		if hasattr(function_with_decorator, "levent_constraints"):
			wrapped_function.levent_constraints = function_with_decorator.levent_constraints
		return wrapped_function
	return decorator_inner_crap

def bt(x):
	bt = getouterframes(currentframe())
	for f in reversed(bt):
		a,b,c,d = getargvalues(f[0])
		line = f[1]+":"+str(f[2])+":"+f[3]+formatargvalues(a,b,c,d)
		debug(line + (("    :    " + x) if (f == bt[0]) else ""))

def ping(level = 1):
	bt = getouterframes(currentframe())
	f = bt[level]
	a,b,c,d = getargvalues(f[0])
	line = f[1]+":"+str(f[2])+":"+f[3]+formatargvalues(a,b,c,d)
	debug(line)

def log(*vargs):
	#ping(2) #for those wherethefuckdoesthatlinecomefrom moments
	x = ', '.join([str(x) for x in vargs])
	text = topics[-1]+(": ")+str(x) # if len(topics)>1 else ""
	debug(text)

def plog(*args):
	#ping(2) #for those wherethefuckdoesthatlinecomefrom moments
	bt = getouterframes(currentframe())
	f = bt[1]
	a,b,c,d = getargvalues(f[0])
	line = f[1]+":"+str(f[2])+":"+f[3]+formatargvalues(a,b,c,d)
	debug(line+" logs: "+' '.join([str(x) for x in args]))

#def catch(fun):
#	try:

"""
@topic("banana")
def dadada(xxx):
	log(xxx)
dadada(3343)
"""

"""
todo:
tlog(topic, stuff...) - override/one-shot topic

i guess the whole topics thing should have python logging handlers as backend
"""

