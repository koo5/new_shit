from __future__ import unicode_literals
from __future__ import print_function
import traceback, logging
from inspect import *
from time import time

#logging is really only for debugging purposes. users will have key/action log frame.

#stickittothemain: todo: lets do the verbosity level thing or rather topics? and argument --log-events?

#https://code.google.com/p/kosciak-misc/source/browse/python/examples/curses/CursesHandler.py?spec=svn145&r=34

debug = print

topics = []

do_topics = False

def topic(text=None):
	"""decorator to put before your function with a logging topic"""
	if text == None:
		text = function_with_decorator.__name__ #todo: add class

	def decorator_inner_crap(function_with_decorator):
		def wrapped_function(*vargs, **kwargs):
			topics.append(text)
			try:
				result = function_with_decorator(*vargs, **kwargs)
			finally:
				topics.pop()
			return result
		#copy useful attributes of the wrapped function to the wrapper
		#should use wraptools instead
		if hasattr(function_with_decorator, "levent_constraints"):
			wrapped_function.levent_constraints = function_with_decorator.levent_constraints
		if do_topics:
			return wrapped_function
		else:
			return function_with_decorator
	return decorator_inner_crap

def topic2(function_with_decorator):
	"""like topic, but uses function name for the topic text"""
	if do_topics:
		text = function_with_decorator.__name__ #todo: add class
		def wrapper_function(*vargs, **kwargs):
			topics.append(text)
			try:
				result = function_with_decorator(*vargs, **kwargs)
			finally:
				topics.pop()
			return result
		return wrapped_function
	else:
		return function_with_decorator


def log(*vargs):
	#ping(2) #for those wherethefuckdoesthatlinecomefrom moments
	text = ', '.join([str(x) for x in vargs])
	debug(time(), ":".join(topics), text)


"""
try:
	from lemon_utils.lemon_logger import topic,topic2,log
except:
	def topic(text=None):
		"a stub"
		def decorator_inner_crap(function_with_decorator):
			return function_with_decorator
		return decorator_inner_crap
	import logging
	logger = logging.Logger(__name__)
	def log(*vargs):
		logger.debug(str(vargs))
"""
