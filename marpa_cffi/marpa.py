# -*- coding: utf-8 -*-

#this file tries to wrap libmarpa into something pythonic, and not specific to lemon
"""
 * 
 * This file is based on Libmarpa, Copyright 2014 Jeffrey Kegler.
 * Libmarpa is free software: you can
 * redistribute it and/or modify it under the terms of the GNU Lesser
 * General Public License as published by the Free Software Foundation,
 * either version 3 of the License, or (at your option) any later version.
 *
 * Libmarpa is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser
 * General Public License along with Libmarpa.  If not, see
 * http://www.gnu.org/licenses/.
 */
"""

from __future__ import unicode_literals
from __future__ import print_function

from .marpa_cffi import *
from .marpa_misc import *
from .marpa_codes import events

marpa_config = ffi.new("Marpa_Config*")
lib.marpa_c_init(marpa_config)
#Always succeeds.


import logging
logger=logging.getLogger("marpa")
log=logger.debug


def tb():
	import traceback
	return (traceback.extract_stack())

from lemon_args import args


from collections import defaultdict



class Grammar(object):
	def __init__(s):
		s.g = ffi.gc(lib.marpa_g_new(marpa_config), lib.marpa_g_unref)
		s.check_config_error()
		assert lib.marpa_g_force_valued(s.g) >= 0
		s.check_config_error()
		#log(s.g)
	
	def check_config_error(s):
		msg = ffi.new("char **")
		assert lib.marpa_c_error(marpa_config, msg) == lib.MARPA_ERR_NONE,  msg

	def check_int(s, result):
		if result == -2:
			s.get_and_log_error()
			tb()
		return result

	def check_null(s, result):
		if result == ffi.NULL:
			s.get_and_log_error()
			raise Exception("NULL")
		return result

	def error_clear(s):
		lib.marpa_g_error_clear(s.g)

	def symbol_new(s):
		#Return value: On success, the ID of a new symbol; On failure, −2.
		r = lib.marpa_g_symbol_new(s.g)
		r = s.check_int(r)
		r = symbol_int(r)
		return r

	def symbol_is_accessible(s, sym):
		assert type(sym) == symbol_int
		r = s.check_int(lib.marpa_g_symbol_is_accessible(s.g, sym))
		assert r != -1
		return r
		
	def symbol_rank_set(s, sym, rank):
		return s.check_int(lib.marpa_g_symbol_rank_set(s.g, sym, rank))

	def rule_rank_set(s, rule, rank):
		return s.check_int(lib.marpa_g_rule_rank_set(s.g, rule, rank))

	def rule_new(s, lhs, rhs):
		return rule_int(s.check_int(lib.marpa_g_rule_new(s.g, lhs, rhs, len(rhs))))

	def sequence_new(s, lhs, rhs, separator=-1, min=1, proper=False):
		return rule_int(s.check_int(lib.marpa_g_sequence_new(s.g, lhs, rhs, separator, min,
		    MARPA_PROPER_SEPARATION if proper else 0)))

	def precompute(s):
		import time
		start_time = time.time()
		r = s.check_int(lib.marpa_g_precompute(s.g))
		log("marpa_g_precompute returned in %s seconds"%str(time.time() - start_time))
		s.print_events()
		return r

	def events(s):
		count = s.check_int(lib.marpa_g_event_count(s.g))
		log('%s events'%count)
		if count > 0:
			result = ffi.new('Marpa_Event*')
			for i in range(count):
				event_type = s.check_int(lib.marpa_g_event(s.g, result, i))
				event_value = result.t_value
				r = event_type, event_value
				#log('event:%s, value:%s',events[event_type],event_value)
				yield r

	def print_events(s):
		for dummy in s.events():
			pass

	def start_symbol_set(s, sym):
		s.check_int( lib.marpa_g_start_symbol_set(s.g, sym) )

	def get_and_log_error(s):
		log_error(lib.marpa_g_error(s.g, ffi.new("char**")))

def log_error(e):
	err = codes.errors[e]
	log(err[0] + " " + repr(err[1]) )#constant + description
	raise (Exception(err[0] + " " + repr(err[1]) ))

class Recce(object):
	def __init__(s, g):
		s.g = g
		s.r = s.g.check_null(lib.marpa_r_new(g.g))
		log(s.r)
	def __del__(s):
		lib.marpa_r_unref(s.r)
	def start_input(s):
		s.g.check_int(lib.marpa_r_start_input(s.r))

	def alternative(s, sym, val, length=1):
		assert type(sym) == symbol_int
		assert type(val) == int
		
		r = lib.marpa_r_alternative(s.r, sym, val, length)
		#Return value: On success, MARPA_ERR_NONE. On failure, some other error code.
		if r != lib.MARPA_ERR_NONE:
			log_error(r)


	def earleme_complete(s):
		s.g.check_int(lib.marpa_r_earleme_complete(s.r))
	def latest_earley_set(s):
		return lib.marpa_r_latest_earley_set(s.r)

class Bocage(object):
	def __init__(s, r, earley_set_ID):
		s.g = r.g
		s.b = s.g.check_null(lib.marpa_b_new(r.r, earley_set_ID))
		log(s.b)
	def __del__(s):
		if 'b' in s.__dict__:
			lib.marpa_b_unref(s.b)

class Order(object):
	def __init__(s, bocage):
		s.g = bocage.g
		s.o = s.g.check_null(lib.marpa_o_new(bocage.b))
		log(s.o)
	def __del__(s):
		lib.marpa_o_unref(s.o)

class Tree(object):
	def __init__(s, order):
		s.g = order.g
		s.t = s.g.check_null(lib.marpa_t_new(order.o))
		log(s.t)
	def __del__(s):
		lib.marpa_t_unref(s.t)
	def nxt(s):
		while True:
			r = s.g.check_int(lib.marpa_t_next(s.t))
			if r == -1:
				break
			yield r

class Valuator(object):
	def __init__(s, tree):
		s.g = tree.g
		s.v = s.g.check_null(lib.marpa_v_new(tree.t))
		log(s.v)
	def __del__(s):
		if s.v != None:
			s.unref()
	def unref(s):
		lib.marpa_v_unref(s.v)
		s.v = None
	def step(s):
		assert s.v
		return s.g.check_int(lib.marpa_v_step(s.v))
		






# http://scipy-lectures.github.io/advanced/debugging/#debugging-segmentation-faults-using-gdb
# http://fpaste.scsys.co.uk/451285 -  typical marpa C calls
#https://github.com/Rizziepit/cffibuilder!      ``
