__author__ = 'kook'

import lemon_platform

if lemon_platform.frontend == lemon_platform.server:
	from tags_fast import *
else:
	from tags_old import *
