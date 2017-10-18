from nodes import *

MLTT = Dotdict()
MLTT._dict = odict()


def build_in_MLTT(r):
	r["MLTT"] = B.builtinmodule.inst_fresh()
	r["MLTT"].ch.statements.items = [
		Comment("""MLTT""")]

	r["MLTT-test"] = B.builtinmodule.inst_fresh()
	r["MLTT-test"].special_scope = [r["MLTT"]];

	freshvarid = [0]

	def genFreshVarName():
		freshvarid[0] += 1
		return Var({'name': RestrictedIdentifier("var" + str(freshvarid[0]))})

	build_in(SyntacticCategory({'name': Text("exp")}), None, MLTT)
	MLTT.exp.help = ["a lambda expression"]

	class DebVar(Compound):
		help = ["a De Brujin-ized variable"]

		@property
		def dist(s):
			return s.ch.dist.pyval

		@property
		def varName(s):
			return s.ch.name.pyval

		@varName.setter
		def varName(s, v):
			s.ch.name.pyval = v

		def __init__(s, children):
			super(Var, s).__init__(children)

	build_in(compound(DebVar,
	                        [ChildTag("name"), ChildTag('dist')],
	                        {'name': B.restrictedidentifier, 'dist': B.number}))

	class Var(Compound):
		brackets = ("", "")
		help = ["a variable"]

		@property
		def varName(s):
			return s.ch.name.pyval

		@varName.setter
		def varName(s, v):
			s.ch.name.pyval = v

		def __init__(s, children):
			super(Var, s).__init__(children)

	build_in(compound(Var,
	                        [ChildTag("name")],
	                        {'name': B.restrictedidentifier}), None, MLTT)

	class ParExp(Compound):
		help = ["a parenthesized expression"]
		brackets = ("", "")

	build_in(compound(ParExp,
	                        [TextTag("("), ChildTag("exp"), TextTag(")")],
	                        {'exp': MLTT.exp}), None, MLTT)

	class PiType(Compound):
		help = ["""function type		"""]

	build_in(compound(PiType,
	                        [
		                        [ChildTag("arg"), TextTag(":"), ChildTag("type"), TextTag("->"), ChildTag("ret")],
	                        ],
	                        {'arg': MLTT.var, 'type': MLTT.exp, 'ret': MLTT.exp}), None, MLTT)

	class Abs(Compound):
		help = ["abstraction, a lambda"]

	build_in(compound(Abs,
	                        [[TextTag("\\"), ChildTag("var"), TextTag(":"), ChildTag("type"), TextTag("."),
	                          ChildTag("exp")]
	                         ],
	                        {'var': MLTT.var, 'type': MLTT.exp, 'exp': MLTT.exp}), None, MLTT)

	class App(Compound):
		help = ["""function application, a call
			#"do" <function> "to" <argument>
			#"run" <function> "on" <argument>
		"""]

	build_in(compound(App,
	                        [[ChildTag("e1"), TextTag(" "), ChildTag("e2")]
	                         ],
	                        {'e1': MLTT.exp, 'e2': MLTT.exp}), None, MLTT)

	class Level(Compound):
		pass

	build_in(compound(Level,
	                        [TextTag("#")],
	                        {}), None, MLTT)

	class Succ(Compound):
		help = ["""the successor of a level"""]

	build_in(compound(
		Succ,
		[[TextTag("+")]],
		{}),
		None,
		MLTT)

	class Set(Compound):
		help = ["""the function constructing an MLTT universe from an element of Level"""]

	build_in(compound(
		Set,
		[[TextTag("*")]],
		{}),
		None,
		MLTT
	)

	class SetOmega(Compound):
		help = ["""the 'kind' of MLTT universes"""]

	build_in(compound(
		SetOmega,

		# eventually instead of TextTag we should extend this into
		# a mechanism for users to customize their display more generally

		[[TextTag("* Omega")]]
		, {}), None, MLTT
	)

	# In this version where (Set Omega) would be interpreted as an App of a function Set,
	# then it kinda makes more sense to interpret Omega as an inaccessible level, and
	# (Set Omega) as the corresponding inaccessible universe, with no type of its own.


	for a, b in [

		(MLTT.parexp, MLTT.exp),
		(MLTT.app, MLTT.exp),
		(MLTT.abs, MLTT.exp),
		(MLTT.var, MLTT.exp),
		(MLTT.pitype, MLTT.exp),
		(MLTT.set, MLTT.exp),
		(MLTT.level, MLTT.exp),
		(B.number, MLTT.exp),
		(MLTT.setomega, MLTT.exp),
		(MLTT.succ, MLTT.exp)

	]: build_in(WorksAs.b(a, b), False, MLTT)

	r["MLTT"].ch.statements.items.extend(list(itervalues(MLTT._dict)))

	def debrujin(node, ctx):
		if type(node) == Var:
			if node.varName in ctx:
				return DebVar(ctx.index(name), name)
			else:
				raise "var is not in scope"
		if type(node) == App:
			return App({'e1': debrujin(node.ch.e1, ctx), 'e2': debrujin(node.ch.e2, ctx)})

		if type(node) == Abs:
			ctx = [node.ch.var.varName] + ctx
			return Abs({'var': debrujin(node.ch.var, ctx), 'type': debrujin(node.ch.type, ctx),
			            'exp': debrujin(node.ch.exp, ctx)})
		if type(node) == PiType:
			ctx = [node.ch.var.varName] + ctx
			return PiType({'var': debrujin(node.ch.var, ctx), 'type': debrujin(node.ch.type, ctx),
			               'exp': debrujin(node.ch.exp, ctx)})

		return node

	# Just need to analyze the control flow here.
	def prove(in_prop, env1=None, env2=None):
		if (env1 == None): env1 = []
		if (env2 == None): env2 = {}

		# Make sure it passes a type-check, and it's type is (Set n), for
		# some Level, n. (Otherwise it's not a proposition!)
		t = nf(type_check(in_prop, env2))

		if (not isinstance(t, SetOmega)):
			if (not isinstance(t, App)):
				print("Can't be a proposition/type if it's not an App")
				assert False

			# ah, i think we need a more liberal definition of Number here
			if ((not isinstance(t.ch.e1, Set)) or (not (isinstance(type_check(t.ch.e2), Level)))):
				print("Can't be a proposition/type if it's not a Set <number>")
				assert False

		# normalize it to reduce the number of different expression classes
		# we have to consider
		prop = nf(in_prop)

		# look up the prop in the 'env'
		# if you find it, then return the associated bound variable
		# if you don't, then proceed to try the PiType case, where
		# we'll actually attempt to construct an Abs as our proof
		# term

		got_something = False
		for i in env1:
			if (betaEq(prop, i[0])):
				got_something = True
				yield i[1]

			# Ok we didn't find it in the 'env', so we attempt to
		# construct a proof term directly.

		# A proof of a PiType is a function with the same
		# domain and range. We get the domain component of the
		# function for free. If the pi-type is (x:X)->_, then
		# automatically our function will be \(x:X).proof(_),
		# if proof(_) exists.
		if isinstance(prop, PiType):
			got_something = True
			tmp_env1 = env1[:]
			tmp_env1.append([prop.ch.type, prop.ch.arg])
			tmp_env2 = dict(env2)
			tmp_env2[prop.ch.arg.varName] = prop.ch.type

			for ppp in prove(prop.ch.ret, tmp_env1, tmp_env2):
				yield Abs({
					'var': prop.ch.arg,
					'type': prop.ch.type,
					'exp': ppp
				})

		# A proof of a (Set n) is (Set (n-1)) if n > 0.
		# What about in the case where n = 0?
		# should this be fixed up to "understand" the relation between
		# Level and Nat ?
		if isinstance(prop, App):
			if (prop.ch.e2.pyval == 0):
				print("Not sure which proof to give you, but there's plenty of them!")
				got_something = True
			else:
				# for type-checking we needed +1, for proving we need -1
				# still need this
				got_something = True
				return App({'e1': Set({}), 'e2': (prop.ch.e2 - 1)})

		# we will get here as well
		# or we need to specify what case should fail

		# well i could hack this up but it would be better if you change the control flow appropriately instead
		elif not got_something:
			print("What exactly are you telling me to prove here? " + prop.tostr(True))

	def set_max(set1, set2):
		# ok so we're assuming max was called with two things that end in a number
		# and not a variable or application of succ's to a variable (cause that would
		# be universe polymorphism and call for set-omega)


		a = nf(set1).ch.e2
		# assert
		assert type(a) == Number
		b = nf(set2).ch.e2
		assert type(b) == Number

		return max(a.pyval, b.pyval)

	def type_check(expr: Node, env=None, level_flag=False):  # returns Node
		# set up an empty list of type assumptions
		if (env == None): env = {}

		# just like normally, we look up the type assumption for the variable
		# in the environment
		if isinstance(expr, Var):
			return env[expr.varName]

		if isinstance(expr, App):
			# type-check-reduce the function using the current
			# environment
			# why whnf vs nf vs nothing?
			print("Type-checking an App")
			print("Type-checking it's function")
			func_t = whnf(type_check(expr.ch.e1, env))

			# functions are supposed to have pi-types. we only
			# allow functions to appear in function-position in
			# applications. so make sure it's type is a pi-type:
			if isinstance(func_t, PiType):
				# if so, type-check the argument expression
				# using the current environment
				print("It's a function; type-checking it's arg")
				arg_t = type_check(expr.ch.e2, env)

				print("Checking if arg-type matches domain")
				if (not (betaEq(func_t.ch.type, arg_t))):
					print("Error: bad argument type")
					assert False

				else:
					print("substitute the argument into the return type")
					return subst(func_t.ch.ret, func_t.ch.arg, expr.ch.e2)
			else:
				print("Error: trying to apply(call) something that's not a function")
				assert False

		# Succ is a function that takes a Level and a returns a Level,
		# so, it's function type is  v:Level -> Level
		if isinstance(expr, Succ):
			v = genFreshVarName()  # wanna make this return a Var?
			# probably
			return PiType({
				'arg': v,
				'type': Level({}),
				'ret': Level({})
			})

		# Set itself is a universe-polymorphic function.
		# it's a function that takes an argument n of type Level
		# and produces an object of type (Set (n+1)), namely
		# (Set n).

		# Any pi-type quantified over Level, and with return-type
		# actually depending on the input, has type SetOmega

		# i dont mind digging into it but im getting tired here, gonna go take a shower now
		# ok sounds good

		# Set :: v:#->(Set (Succ v))
		# Set i :: (Set (Succ i))

		# This rule combines with the rules for App, Succ, Level & Number
		if isinstance(expr, Set):
			v = genFreshVarName()
			# so Var has name Text?
			# gotta keep in mind we deal with lemon nodes here,
			# im just not sure what the lc's syntax supposed to be

			return PiType({
				'arg': v,
				'type': Level({}),
				'ret': App({
					'e1': Set({}),
					'e2': App({
						'e1': Succ({}),
						'e2': v
					})
				})
			})

		if isinstance(expr, Abs):
			# make sure that the type of the bound variable is actually
			# a type, in this context.
			type_check(expr.ch.type, env)

			# copy the set of type assumptions into a new set
			tmp_env = dict(env)

			# add a type assumption for the bound variable to the
			# new set
			tmp_env[expr.ch.var.varName] = expr.ch.type

			# type-check the body of the abstraction using the new
			# set of type assumptions
			expr_t = type_check(expr.ch.exp, tmp_env)

			# abstractions have Pi-types as their types
			rt = PiType({'arg': expr.ch.var, 'type': expr.ch.type, 'ret': expr_t})

			# now that we've constructed the pi-type for our lambda abstraction,
			# we're going to type-check the pi-type itself and make sure it
			# passes.

			# this probably isn't necessary in full MLTT with universe polymorphism
			# cause all possibilities are allowed already, and this extra type_check
			# is just to make sure that the PiType of our Abs fits one of the allowedKinds
			# (allowedKinds should really be called allowedDependencies)

			# shouldn't hurt anything to have it though, and if it does, then that will
			# be indication that we messed something up
			type_check(rt, env)

			# return the pi-type if it passes the type-check
			return rt

		if isinstance(expr, PiType):

			print("Pi-type: ", expr.tostr())
			# type-check-reduce the input type
			# why whnf vs nf vs nothing?
			s = whnf(type_check(expr.ch.type, env))

			print("s = ", s.tostr())
			# Universe polymorphism always begins when we quantify over
			# Level.
			# Not everything that quantifies over Level is necessarily universe-polymorphic
			# though.
			# For example "n:Level -> Level"
			# there's certainly no polymorphism happening here at all
			# Otoh, "n:Level->(Set n)" is most definitely universe-polymorphic.

			# What's the difference? a) the return type depends on the level variable n
			# Moreover, it depends on the level-variable in order to construct (Set n)
			#
			# In general: a pi-type represents a universe polymorphism if it quantifies
			# over Level, and the return type depends on the Level variable n

			# The only way to construct types from Level's is through "Set" (i think?)
			# so, if the return type of a pi-type depends on the Level variable n, and
			# it is actually a type, then n must be used in the form "Set n". (am i sure
			# there isn't any other possibility?)

			# We know for a fact:
			# If the pi-type quantifies over Level, n, and the return type contains
			# (Set n) as a sub-expression, then our pi-type is universe-polymorphic
			# and has type SetOmega, (assuming the rest of the expression passes type-checking)

			# n:#->(t:(* n)->(x:t->t))

			# type-checking "x:t->t" in the context "{n:#, t:(* n)}"
			#	s = (* n), t = (* n)

			# maybe i should add in a symbolic max() function
			# set_max((* m), (* n)) = (* (max m n))
			# l = level_flag
			# if isinstance(expr.ch.type,Level):
			#	print("Starting universe polymorphism, plase stand by...")
			#	l = True
			# if l:
			# we know the type is gonna be SetOmega if it's
			# well-formed, but we still need to check the rest
			# of the expression to make sure it's well-formed.
			#	print("Using universe polymorphism")
			# copy the set of type assumptions into a new set
			tmp_env = dict(env)

			# add a type assumption for the bound variable to
			# the new set
			tmp_env[expr.ch.arg.varName] = expr.ch.type

			# type-check-reduce the body of the abstraction
			# using the new set of type assumptions
			# why whnf vs nf vs nothing?
			t = whnf(type_check(expr.ch.ret, tmp_env))
			print("t = ", t.tostr())
			s_level = -1
			t_level = -1
			if (isinstance(s, App) and isinstance(s.ch.e1, Set)):
				print("s.ch.e2: ", s.ch.e2.tostr())
				nfs = nf(s.ch.e2)
				print("nfs: ", nfs.tostr())
				# Set 5
				if isinstance(nfs, Number):
					s_level = s.ch.e2.pyval

				# Set n, or Set (Succ (Succ n))
				elif type(nfs) in [Var, App]:
					print("s is universe-polymorphic")
					return SetOmega({})

				else:
					print("What kind of Set is this?", s.ch.e2.tostr())
					assert False
			elif isinstance(s, SetOmega):
				print("s is SetOmega")
				return SetOmega({})
			else:
				print("The type of your type is not a type!")
				assert False

			if (isinstance(t, App) and isinstance(t.ch.e1, Set)):
				print("t.ch.e2: ", t.ch.e2.tostr())
				nft = nf(t.ch.e2)
				print("nft: ", nft.tostr())
				if isinstance(nft, Number):
					t_level = t.ch.e2.pyval

				if type(nft) in [Var, App]:
					print("t is universe-polymorphic")
					return SetOmega({})
				else:
					print("What kind of Set is this?", t.ch.e2.tostr())
					assert False
			elif isinstance(t, SetOmega):
				print("t is SetOmega")
				return SetOmega({})
			else:
				print("The type of your type is not a type!")
				assert False
			# n:#->(t:(* n)->(x:t->t)) : [s=(* 0), t=SetOmega]
			# "#" type-checks to (* 0)
			# "t:(* n)->(x:t->t) type-checks to SetOmega

			# t:(* n)->(x:t->t) : [s=SetOmega,t=SetOmega]
			# "(* n)" type-checks to SetOmega
			# "x:t->t" type-checks to [(* n),(* n)]

			# x:t->t : [s=SetOmega,t=SetOmega]
			# "t" type-checks to "(* n)"
			# "t" type-checks to "(* n)"
			if (s_level < 0):
				print("s: Negative set-level?")
				assert False
			if (t_level < 0):
				print("t: Negative set-level?")
				assert False
			return App({'e1': Set({}), 'e2': Number(max(s, t))})

		if isinstance(expr, Number):
			print("Type-checking a number")
			return Level({})

		if isinstance(expr, Level):
			# in Agda, Level has type (Set 0)
			print("zero it baby")
			return App({'e1': Set({}), 'e2': Number(0)})

		if isinstance(expr, SetOmega):
			print("Error: SetOmega has no type!")
			assert False

	def FreeVars(expr, vars=None) -> set:
		if (vars == None): vars = set()

		# if the expression is a variable, add it
		# to the list of free variables. so what
		# happens to bound variables? they get removed
		# from the list in the abstraction case.
		if isinstance(expr, Var):
			vars.add(expr.varName)
			return vars

		# the free variables of an application is
		# the union of the free variables in each
		# of its components (function and argument)
		if isinstance(expr, App):
			free_e1 = FreeVars(expr.ch.e1, vars)
			return free_e1.union(FreeVars(expr.ch.e2, vars))

		# we don't care whether the variables are occurring
		# in an expression or its type, we just care where
		# variables are occurring, cause when we get into
		# the full lambda MLTT dependencies, things can be
		# going everywhere

		# the free variables of a typed abstraction is
		# the union of the free variables in it's input-type
		# component with the free variables in it's body
		# component, with the bound variable removed
		if isinstance(expr, Abs):
			free_t = FreeVars(expr.ch.type, vars)
			free_e = FreeVars(expr.ch.exp, vars)

			if (expr.ch.var.varName in free_e):
				free_e.remove(expr.ch.var.varName)
			return free_t.union(free_e)

		# the free variables of a pi-type is the union
		# of the free variables in it's input-type component
		# with the free variables in it's body component,
		# with the bound variable removed
		if isinstance(expr, PiType):
			free_t = FreeVars(expr.ch.type, vars)
			free_e = FreeVars(expr.ch.ret, vars)

			if (expr.ch.arg.varName in free_e):
				free_e.remove(expr.ch.arg.varName)
			return free_t.union(free_e)

		# these are constants and don't contain any variables,
		# just return the current list of free vars
		if type(expr) in [Set, Level, Number]:
			return vars

		if isinstance(expr, SetOmega):
			# this is probably an error, but i'm not 100%
			print("Is FreeVars(SetOmega) an error? Maybe, so let's crash.")
			assert False

	# substitute "what" with "by" in "where"
	# he says his is is subst(what,where,by)
	# or                subst(v,   x,    e)
	#
	# but it's really   subst(what,by,where)
	def subst(where: Node, what: Node, by: Node):
		print("subst()")
		for x in where, what, by:
			assert isinstance(x, Node), x
		# if the 'where' expression is the var that we're
		# substituting, then make the substitution, otherwise
		# just return 'where'.
		if isinstance(where, Var):
			print("subst var()")
			if (where.varName == what.varName):
				return by
			else:
				return where

		# make the substitution into both the function and the argument
		# in an application
		if isinstance(where, App):
			print("subst app()")
			return App({'e1': subst(where.ch.e1, what, by), 'e2': subst(where.ch.e2, what, by)})

		if isinstance(where, Abs):
			print("subst abs()")
			# if the bound variable of the abstraction is the var
			# we're supposed to be substituting, then i guess we
			# say this new occurrence of a bound variable with the
			# same name shadows the substitution-variable in the
			# body expression. however, we still might be making the
			# substitution in the expression for the input-type of
			# the abstraction (i.e. dependent types & type operators)
			if (where.ch.var.varName == what.varName):
				return Abs({
					'var': where.ch.var,
					'type': subst(where.ch.type, what, by),
					'exp': where.ch.exp
				})

			# else if the bound variable of the abstraction is in
			# the free variables of the 'by' expression, then
			# replace the bound variable in the abstraction with a
			# fresh variable so that it won't interfere with the
			# free variables in 'by'. then substitute 'by' for 'what'
			# in both the input-type and the abstraction body
			elif (where.ch.var.varName in FreeVars(by)):
				z = genFreshVarName()
				t1 = subst(where.ch.exp, where.ch.var, z)
				return Abs({
					'var': z,
					'type': subst(where.ch.type, what, by),
					'exp': subst(t1, what, by)
				})

			# else we can just make the substitution directly since
			# there's no free-variable interference or scoping/shadowing
			# issues:
			else:
				return Abs({
					'var': where.ch.var,
					'type': subst(where.ch.type, what, by),
					'exp': subst(where.ch.exp, what, by)
				})

		# Pi's should work just like Abs
		if isinstance(where, PiType):
			print("subst pi()")
			if (where.ch.arg.varName == what.varName):
				return PiType({
					'arg': where.ch.arg,
					'type': subst(where.ch.type, what, by),
					'ret': where.ch.exp
				})

			elif (where.ch.arg.varName in FreeVars(by)):
				z = genFreshVarName()
				t1 = subst(where.ch.ret, where.ch.arg, z)
				return PiType({
					'arg': z,
					'type': subst(where.ch.type, what, by),
					'ret': subst(t1, what, by)
				})

			else:
				return PiType({
					'arg': where.ch.arg,
					'type': subst(where.ch.type, what, by),
					'ret': subst(where.ch.ret, what, by)
				})

		# * and [] both don't contain any vars so you're not gonna
		# substitute anything into them. return the expression as is.
		if type(where) in [Set, Level, Number, Succ]:
			print("subst constant()")
			return where
		if isinstance(where, SetOmega):
			print("Is subst(SetOmega) an error? Maybe, so let's crash.")
			assert False
		# this is probably an error

	# Alpha equivalence: check if the two expressions are
	# equivalent under variable renaming.
	def alphaEq(expr1, expr2):
		print("alphaEq()")
		if (type(expr1) != type(expr2)): return False

		# ok, so this looks like it's explicitly *not* checking
		# if it's equivalent under renaming, since it's checking
		# if the names are equal.

		# this is accounted for by the rest of the function
		# when we encounter lambdas, we transform the 2nd expression
		# so that it's bound variable matches that of the 1st

		# that being said, i noticed some people in the comments
		# were pointing out small mistakes here and there, so once
		# we have it all down we might be on our own in ensuring that
		# it's 100% correct (not just this function but the whole thing)

		# what happens if it just gets two variables as the argument
		# expressions? no renaming happens so we'd fail alphaEq
		# in untyped lambda calculus we can have vars outside of
		# abstractions
		if (type(expr1) == Var):
			return (expr1.varName == expr2.varName)

		# App is simple enough, just check if both the functions
		# are alpha equivalent and if both the arguments are
		# alpha equivalent
		if (type(expr1) == App):
			return (alphaEq(expr1.ch.e1, expr2.ch.e1)
			        and alphaEq(expr1.ch.e2, expr2.ch.e2)
			        )

		# Two abstractions with different bound variables can
		# mean the same thing, i.e. they would be the same
		# under a suitable variable renaming.

		# check if the input types are alpha equivalent, then
		# replace the bound variable in the second abstraction
		# with the bound variable from the first lambda abstraction
		# and see if their bodies are syntactically equal

		# the syntactic equality is enforced by recursing down to the
		# Var case above
		if (type(expr1) == Abs):
			return (alphaEq(expr1.ch.type, expr2.ch.type)
			        and alphaEq(
				expr1.ch.exp,
				subst(expr2.ch.exp, expr2.ch.var, expr1.ch.var)
			)
			        )

		# dependent function types
		# \x:t.x->x.
		# not sure how to construct a type using terms.
		#
		# check if the input types are equal
		# replace the bound variable in the second pi-type
		# with the bound variable from the first and check
		# if their bodies are alpha-equivalent.
		if (type(expr1) == PiType):
			return (alphaEq(expr1.ch.type, expr2.ch.type)
			        and alphaEq(
				expr1.ch.ret,
				subst(expr2.ch.ret, expr2.ch.arg, expr1.ch.arg)
			)
			        )
		# Singleton classes of Constants
		if type(expr1) in [Set, Level, SetOmega]:
			return True

		# hrm, i started setting it up to work with a Succ function
		# and was thinking of how to get it to ... "understand" the
		# relation between the numbers defined through Succ, the numbers
		# defined as B.number, and.. maybe the church-encoded natural
		# numbers.., but,
		# for now i should probably switch that stuff out with just B.number
		# to keep it simple
		# but.. i guess the reason i started doing it like that was the
		# Succ form allowed me to use variable numbers, like, (Set n) and
		# Set (Succ n),
		# in the lc code you mean?
		# could it be as simple as having Succ evaluate to Number(arg.pyval+1)?
		# well, it comes up when type-checking universe-polymorphic functions
		# you have a variable number in the type-checking process, even though
		# we don't intend to use Succ directly in the lc (at least, allowing that
		# is an independent issue i guess)
		if isinstance(expr1, Number):
			return (expr1.pyval == expr2.pyval)
		# it is not an error to find SetOmega here

	# reduce both expressions to normal form and then check if they are
	# alpha-equivalent
	def betaEq(expr1, expr2):
		print("betaEq()")

		v = alphaEq(nf(expr1), nf(expr2))
		print(v)
		return v

	# return the normal form of the expression
	def nf(expr):
		print("nf", expr.tostr())
		if type(expr) in [Var, Set, Succ, Level, SetOmega, Number]:
			return expr

		if isinstance(expr, App):
			nf1 = nf(expr.ch.e1)
			if type(nf1) in [Set]:
				return App({'e1': Set({}), 'e2': nf(expr.ch.e2)})
			if isinstance(nf1, Succ):
				nf2 = nf(expr.ch.e2)
				if type(nf2) == Number:
					return Number(nf2.pyval + 1)
				else:
					return App({'e1': nf1, 'e2': nf2})

				# the nf of expr.ch.e2 will be either a Number,
				# a var, or an application of succ's to a var.

				# we won't have application of succ's to a Number
				# cause those will be added up by the Number case

				# if it ends in a var, instead of have succ, succ, succ...
				# we could condense that into something which keeps track of
				# how much is supposed to be added to a var, idk
				# i'm still working through all the details with this bit of it
				# i guess that would be an application of addition
				# well, this version should at least work, even if it's not necessarily
				# a speed demon

				# so at the end is either:
				# a Number
				# a Zero?
				# something else?
				# i guess a Var
				# ok it will crash and burn if we Succ something else
			if isinstance(nf1, Abs):
				return nf(subst(nf1.ch.exp, nf1.ch.var, expr.ch.e2))

			else:
				print("What are you trying to normalize here?")
				assert False

		if isinstance(expr, Abs):
			return Abs({'var': expr.ch.var, 'type': nf(expr.ch.type), 'exp': nf(expr.ch.exp)})

		if isinstance(expr, PiType):
			return PiType({'arg': expr.ch.arg, 'type': nf(expr.ch.type), 'ret': nf(expr.ch.ret)})

	# return the "weak head normal form" of the expression

	def whnf(expr):
		print("whnf()")
		# variables, abstractions, and pi-types are already in weak-head normal form
		# so just return them
		if type(expr) in [Var, Abs, PiType, Set, Level, SetOmega, Number]:
			return expr

		# if it's an application then we check whether there's an
		# application or an abstraction in the function position
		# (it shouldn't be anything else)
		if isinstance(expr, App):
			# if it's an abstraction in function position, then
			# we apply it to the argument.
			# need to make sure the value we get as a result of this
			# is also in weak-head normal form.
			# i don't think he does this in "simpler, easier"
			if type(expr.ch.e1) in [Set, Succ]:
				return expr

			if isinstance(expr.ch.e1, Abs):
				return whnf(subst(expr.ch.e1.ch.exp, expr.ch.var, expr.ch.e2))

			# if it's an application in function position, then
			# we whnf() that application and return a new application
			# that has this new expression as e1, but the same argument
			# for e2
			if isinstance(expr.ch.e1, App):
				return App({'e1': whnf(expr.ch.e1), 'e2': expr.ch.e2})


			else:
				print("What are you trying to normalize here?")
				assert False

		else:
			print("What are you trying to normalize here?")
			assert False

	ParExp.unparen = lambda s: s.ch.exp.unparen()

	def eval(e):
		x = e.copy().unparen()
		# print (x.tostr())
		n = nf(x)
		assert n
		return n.copy()

	for x in [ParExp, App, Abs, Var, PiType, Set, Level, SetOmega, B.number]: x._eval = eval
	for x in [ParExp, App, Abs, Var, PiType, Set, Level, SetOmega, B.number]: x.type_check = type_check
	for x in [ParExp, App, Abs, Var, PiType, Set, Level, SetOmega, B.number]: x.prove = prove

