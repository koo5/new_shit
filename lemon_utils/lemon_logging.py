from __future__ import unicode_literals
from __future__ import print_function
import traceback, logging
from inspect import *
from time import time
import logging
import sys

logger = logging.Logger('lemon')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stderr)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

#log = logger.debug
warn = logger.warning
info = logger.info

def log(format_string, *vargs):
	"backwards compatibility with my old system"
	if __debug__:
		try:
			text = format_string % vargs
		except:
			text = str((format_string, vargs))
		logger.debug(text)



#https://docs.python.org/3/howto/logging-cookbook.html
#https://code.google.com/p/kosciak-misc/source/browse/python/examples/curses/CursesHandler.py?spec=svn145&r=34

#http://stackoverflow.com/questions/533048/extend-standard-python-logging-to-include-the-line-number-where-a-log-method-wa
#->replace old log() calls with log(str()) and go?