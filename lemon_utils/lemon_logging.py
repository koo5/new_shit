from __future__ import unicode_literals
from __future__ import print_function
import traceback, logging
from inspect import *
from time import time
import logging
logger = logging.Logger(__name__)


def log(format_string, *vargs):
	if __debug__:
		try:
			text = format_string % vargs
		except:
			text = str((format_string, vargs))
		logger.debug((time(), text))


def warn(format_string, *vargs):
	log("WARNING:"+format_string, vargs)

#https://code.google.com/p/kosciak-misc/source/browse/python/examples/curses/CursesHandler.py?spec=svn145&r=34
