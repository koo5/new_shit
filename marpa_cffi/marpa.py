from cffi import FFI

ffi = FFI()


ffi.cdef(open("marpa.h.cffi.h", "r").read())


lib = ffi.verify("""
#include <marpa.h>
""", libraries=['marpa'])


print lib


assert lib.MARPA_MAJOR_VERSION == lib.marpa_major_version
assert lib.MARPA_MINOR_VERSION == lib.marpa_minor_version
assert lib.MARPA_MICRO_VERSION == lib.marpa_micro_version
#ver = ffi.new("int [3]")
#lib.marpa_version(ver)


assert lib.marpa_check_version (lib.MARPA_MAJOR_VERSION ,lib.MARPA_MINOR_VERSION, lib.MARPA_MICRO_VERSION ) == lib.MARPA_ERR_NONE


from error_names import err


config = ffi.new("Marpa_Config*")
lib.marpa_c_init(config)
#Always succeeds.

class grammar(object):
	def __init__(s):
		s.g = ffi.gc(lib.marpa_g_new(config), lib.marpa_g_unref)
		s.check_config_error()
		assert lib.marpa_g_force_valued(s.g) >= 0
		s.check_config_error()
		#print s.g
	
	def check_config_error(s):
		msg = ffi.new("char **")
		assert lib.marpa_c_error(config, msg) == lib.MARPA_ERR_NONE,  mss

	def check_int(s, result):
		if result == -2:
			e = lib.marpa_g_error(s.g, ffi.new("char**"))
			assert e == lib.MARPA_ERR_NONE,  err[e]
		return result
		
	def error_clear(s):
		lib.marpa_g_error_clear(s.g)

	def symbol_new(s):
		return symbol(s)
	
	def rule_new(s, lhs, rhs):
		return rule(s, lhs, rhs)

	def precompute(s):
		s.check_int(lib.marpa_g_precompute(s.g))

class symbol(object):#?
	def __init__(s, g):
		s.g = g
		s.s = g.check_int(lib.marpa_g_symbol_new(g.g))
	def start_symbol_set(s):
		s.g.check_int( lib.marpa_g_start_symbol_set(s.g.g, s.s) )

class rule(object):
	def __init__(s, g, lhs, rhs):
		s.r = g.check_int(lib.marpa_g_rule_new(g.g, lhs.s, [i.s for i in rhs], len(rhs)))

class recce(object):
	def __init__(s, g):
		s.g = g
		s.r = lib.marpa_r_new(g.g)
	def __del__(s):
		lib.marpa_r_unref(s.r)
	def start_input(s):
		s.g.check_int(lib.marpa_r_start_input(s.r))
	def alternative(s, sym, val, length):
		r = lib.marpa_r_alternative(s.r, sym.s, val, length)
		if r != lib.MARPA_ERR_NONE:
			print err[r]
	def earleme_complete(s):
		if lib.marpa_r_earleme_complete(s.r) == -2:
			print "errrrrrrr"
	def latest_earley_set(s):
		return lib.marpa_r_latest_earley_set(s.r)

class bocage(object):
	def __init__(s, r, earley_set_ID):
		s.g = r.g
		s.b = lib.marpa_b_new(r.r, earley_set_ID)
		print s.b
	def __del__(s):
		lib.marpa_b_unref(s.b)

class order(object):
	def __init__(s, bocage):
		s.o = lib.marpa_o_new(bocage)
		print s.o
	def __del__(s):
		lib.marpa_o_unref(s.o)

class tree(object):
	def __init__(s, order):
		s.t = lib.marpa_t_new(order)
		print s.t
	def __del__(s):
		lib.marpa_t_unref(s.t)
	def nxt(s):
		r = check_int(lib.marpa_t_next(s.t))
		if r != -1:
			yield r

class valuator(object):
	def __init__(s, tree):
		s.v = lib.marpa_v_new(tree)
		print s.v
	def __del__(s):
		lib.marpa_v_unref(s.v)
	def step(s):
		r = check_int(lib.marpa_v_step(s.v))
		

def test1():
	class SimpleNamespace:
		def __init__(self, pairs):
			self.__dict__.update(pairs)
		def __repr__(self):
			keys = sorted(self.__dict__)
			items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
			return "{}({})".format(type(self).__name__, ", ".join(items))

	g = grammar()


	sy = SimpleNamespace([(name, g.symbol_new()) for name in "S E op number".split()])
	sy.S.start_symbol_set()
	rules = SimpleNamespace([(name, g.rule_new(lhs, rhs)) for name, lhs, rhs in [
		('start', sy.S, [sy.E]),
		('op'    , sy.E, [sy.E, sy.op, sy.E]),
		('ident' , sy.E, [sy.number])]])
	
	g.precompute()
	
	r = recce(g)
	r.start_input()

	print g,r
	
	codes = [(sy.number, 2),(sy.op, ord('-')),(sy.number, 1),(sy.op, ord('*')),
		(sy.number, 3),(sy.op, ord('+')),(sy.number, 1)]
	
	for (sym, val) in codes:
		r.alternative(sym, val, 1)
		r.earleme_complete()

	latest_earley_set_ID = r.latest_earley_set()
	print latest_earley_set_ID
	b = bocage(r, latest_earley_set_ID)
	

test1()
