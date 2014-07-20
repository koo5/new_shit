import traceback, logging
from inspect import *

#stickittothemain: todo: lets do the verbosity level thing or rather topics? and argument --log-events?

#logging is really only for debugging purposes. users will have key/action log frame.

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
	logging.debug(x)

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
function decorator that sets default logging_topic function-wise. should make topics available for args help
tlog(topic, stuff...) - an override/one-shot
i guess this is doable with python logger objects.
"""
