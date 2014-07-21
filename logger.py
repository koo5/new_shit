import traceback, logging
from inspect import *

#logging is really only for debugging purposes. users will have key/action log frame.

#stickittothemain: todo: lets do the verbosity level thing or rather topics? and argument --log-events?

topics = [""]

class topic(object):
	"""decorator"""
	def __init__(s, topic):
		s.topic = topic
	def __call__(s, function):
		"""this gets called right after init"""
		def wrapper(*vargs):
			topics.append(s.topic)
			r = function(*vargs)
			topics.pop()
			return r
		return wrapper

@topic("banana")
def dadada(xxx):
	print xxx

dadada(3343)

logging.basicConfig(level=logging.DEBUG, format='%(message)s')

def bt(x):
	bt = getouterframes(currentframe())
	for f in reversed(bt):
		a,b,c,d = getargvalues(f[0])
		line = f[1]+":"+str(f[2])+":"+f[3]+formatargvalues(a,b,c,d)
		logging.debug(line + (("    :    " + x) if (f == bt[0]) else ""))

def ping(level = 1):
	bt = getouterframes(currentframe())
	f = bt[level]
	a,b,c,d = getargvalues(f[0])
	line = f[1]+":"+str(f[2])+":"+f[3]+formatargvalues(a,b,c,d)
	logging.debug(line)

def log(x):
	#ping(2) #for those wherethefuckdoesthatlinecomefrom moments
	logging.debug(topics[-1]+(": " if len(topics)>1 else "")+str(x))

def plog(*args):
	#ping(2) #for those wherethefuckdoesthatlinecomefrom moments
	bt = getouterframes(currentframe())
	f = bt[1]
	a,b,c,d = getargvalues(f[0])
	line = f[1]+":"+str(f[2])+":"+f[3]+formatargvalues(a,b,c,d)
	logging.debug(line+" logs: "+' '.join([str(x) for x in args]))

#def catch(fun):
#	try:

"""
todo:
tlog(topic, stuff...) - override/one-shot topic

i guess the whole topics thing should have python logging handlers as backend
"""
