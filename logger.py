import traceback, logging
from inspect import *

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

#def catch(fun):
#	try:
