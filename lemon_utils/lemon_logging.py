#import traceback,
#from inspect import *
#from time import time
import sys
import logging
from pprint import pformat as pp

logger = logging.Logger('lemon')
logger.setLevel(logging.WARNING)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stderr)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

f = logging.Formatter(
	'%(asctime)s %(module)s:%(lineno)d : %(message)s', '%H:%M:%S')
"""
class PrettyPrintingFormatter(logging.Formatter):
	def formatMessage(self, record):
		print (record.__dict__)
		record.args = tuple([pp(i) for i in record.args])
		return self._style.format(record)

f = PrettyPrintingFormatter()
"""
ch.setFormatter(f)
log = logger.debug
warn = logger.warning
info = logger.info



#https://docs.python.org/3/howto/logging-cookbook.html
#https://code.google.com/p/kosciak-misc/source/browse/python/examples/curses/CursesHandler.py?spec=svn145&r=34

#http://stackoverflow.com/questions/533048/extend-standard-python-logging-to-include-the-line-number-where-a-log-method-wa
#->replace old log() calls with log(str()) and go?