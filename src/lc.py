from nodes import *








lc1 = Dotdict() #a helper dict to hold the nodes being built in and to reference them easily
lc1._dict = odict()


#interesting vim glitch made it look like it was commented out
#if i search "/def build_in_lc(" from the top, i guess it doesn't
#parse the whole file but sees this \"\"\" above
#scroll up and back down and it goes away
def build_in_lc1(r):
	"""creates a new module with definitions for a language separate from
	the lemon stuff
	eventually, this would all be just data in lemon,
	but for now, we "build it in"
	"""
	

	r["lc1"] = B.builtinmodule.inst_fresh()
	r["lc1"].ch.statements.items = [
		Comment("""untyped lambda calculus""")]

	""" whats the lc1-test for """
	#well the gui shows a "root", a tree with a couple of entries,
	#so thats like where you would type in your lambda calculus program	
	r["lc1-test"] = B.builtinmodule.inst_fresh()
	r["lc1-test"].special_scope = [r["lc1"], 
		#B.restrictedidentifier#i will remove this once Syntaxed parser is done, its only to pull in the grammar
		];
		
		

	build_in(SyntacticCategory({'name': Text("exp")}), None, lc1)
	lc1.exp.help = ["a lambda expression"]
	

	class Var(Syntaxed):
		brackets = ("", "")
		help = ["a variable"]
		@property
		def varName(s):
			return s.ch.name.pyval
		@varName.setter
		def varName(s, v):
			s.ch.name.pyval = v
		
	build_in(SyntaxedNodecl(Var,
		[ChildTag("name")],
		{'name': B.restrictedidentifier}), None, lc1)
	#what's B.identifier
	#like we use the lc1 here, B is the main global builtins
	#ah, and i guess identifier is just what we want a name to be?yea

	lc1.var.example = lc1.var.inst_fresh()
	lc1.var.example.ch.name.text = "x"



	class ParExp(Syntaxed): 
		help = ["a parenthesized expression"]
		brackets = ("", "")
		
	build_in(SyntaxedNodecl(ParExp,
		[TextTag("("), ChildTag("exp"), TextTag(")")],
		{'exp': lc1.exp}), None, lc1)
	build_in(WorksAs.b(lc1.parexp, lc1.exp), False, lc1)



	class Abs(Syntaxed): 
		help = ["abstraction, a lambda"]
		#def eval(s):
		
		
		
	build_in(SyntaxedNodecl(Abs,
		[TextTag("\\"), ChildTag("var"), TextTag("."), ChildTag("exp")],
		{'var': lc1.var, 'exp': lc1.exp}), None, lc1)




	class App(Syntaxed): 
		help = ["function application, a call"]
		pass
	build_in(SyntaxedNodecl(App,
		[ChildTag("e1"), TextTag(" "), ChildTag("e2")],
		{'e1': lc1.exp, 'e2': lc1.exp}), None, lc1)


	build_in(WorksAs.b(lc1.app, lc1.exp), False, lc1)
	build_in(WorksAs.b(lc1.abs, lc1.exp), False, lc1)
	build_in(WorksAs.b(lc1.var, lc1.exp), False, lc1)


	r["lc1"].ch.statements.items.extend(list(itervalues(lc1._dict)))
	




	Var.unparen = lambda s: s
	App.unparen = Abs.unparen = lambda s: s.__class__(dict([(k, v.unparen()) for k, v in iteritems(s.ch._dict)]))
	ParExp.unparen = lambda s: s.ch.exp.unparen()
	
	
	#//aka evaluate
	#//Normal order:
	def normalize (e) :
		if isinstance(e, Var):
			return e
			
		if isinstance(e, Abs):
			#return Abs({'var': e.ch.var.copy(), e.ch.exp.eval()})
			return Abs({'var': e.ch.var, 'exp': e.ch.exp.eval()})
			
		if isinstance(e, App):
			if isinstance(e.ch.e1, Abs):
				#//one-step evaluation:
				
				#return subst(e.ch.e1.ch.e2, e.ch.e1.ch.e1, e.ch.e2)
				return subst(e.ch.e1.ch.exp, e.ch.e1.ch.var, e.ch.e2)
				
				#//full evaluation:
				#return subst(e3,x,e2).eval()
				#return subst(e.ch.e1.ch.exp, e.ch.e1.ch.var, e.ch.e2).eval()
				
			if isinstance(e.ch.e1, App):
				#//one step eval or no-op
				tmp = e.ch.e1.eval()
				return App({'e1': tmp, 'e2' : e.ch.e2})
				
				#//definite one step evaluation:
				#not a no-op unless it's in normal form
				#tmp = e.ch.e1.eval()
				#if(tmp == e.ch.e1)
				#	return App({'e1': e.ch.e1, 'e2': e.ch.e2.eval()})
				#else
				#	return App({'e1': tmp, 'e2': e.ch.e2})
				
				
				#//full evaluation:
				#tmp = e.ch.e1.eval()
				
				#only run subst if tmp is an Abs
				
				#if isinstance(tmp, Abs):
				#	return subst(tmp.ch.exp,tmp.ch.var,e.ch.e2).eval()
				#else
				#	return App({'e1': tmp, 'e2': e.ch.e2.eval()})
					
			return e
		assert False, "normalize"


	def eval(e):
		x = e.copy().unparen()
		print (x.tostr())
		n = normalize(x)
		assert n
		return n.copy()

	ParExp.eval = App.eval = Abs.eval = Var.eval = eval


	freshvarid = [0]
	def genFreshVarName():
		freshvarid[0] += 1
		return "var" + freshvarid[0]


	def subst( where, what:Var, by):#e1,x,e2):
		print ("subst where", where.tostr(), "what", what.tostr(), "by", by.tostr())
		if isinstance(where, Var):
			#(Var x)[x := r]         = r
			if (where.varName == what.varName):
				return by
			#(Var y)[x := r]         = y 
			#i'm thinking more like this case
			else:
				return where
		if isinstance(where, App):
			#(App t s)[x := r]       = (t[x:=r])(s[x:=r])
			return App({'e1': subst(where.ch.e1, what, by), 'e2': subst(where.ch.e2, what, by)})
		if isinstance(where, Abs):
			#(Abs x t)[x := r]       = (Abs x t).
			#i think this should be where.ch.var.varName?
			#ah, yea
			# guess we never called an example that used it
			#name would be "RestrictedIdentifier" i think
			#i'm actually still a bit confused about this
			#case myself, but it's what the capture-avoiding
			#substitution rules say to do, *shrug*
			if(where.ch.var.varName == what.varName):
				print ("where is what so fuck you")
			#this would happen in a case like:
			#(\x.(\x.x)) y
			#to evaluate this we're gonna "replace all
			#occurences of 'x' in (\x.x) with 'y'"
			#but i guess the inner \x is taken to be
			# a different var than the outer \x
			
				return where
			else:
				#(Abs y t)[x := r]                                                                
				#if(y not in FreeVars(r))
				
				print("where.var:", where.ch.var.varName, "FreeVars(by):",FreeVars(by))
				if(where.ch.var.varName not in FreeVars(by)):
					print ("var not in freevars")
					#(Abs y subst(t,x,r))
					return Abs({'var':where.ch.var, 'exp': subst(where.ch.exp, what, by)}) 
				else:
					print ("var in freevars")
					z = genFreshVarName()

					#t' = subst(t,y,z)
					t1 = subst(where.ch.exp,where.ch.var,z)

					#t'' = subst(t',x,r)
					t2 = subst(t1,what,by)

					#return (Abs z t'')
					return Abs({'var': z, 'exp': t2})
		assert False, ("subst", where, what, by)
		
		
	
	def FreeVars(expr,vars=None) -> set:
		#shall we save varNames only?
		#we could do that, name is all the structure they have
		#otherwise this set magic wont work so magically
		#standard implementations would do something like
		#de bruijn indexes, i.e. just replace them with numbers

		if vars==None: vars = set()
		print("freevars", expr.tostr(), "vars:", vars)
		
		if isinstance(expr,Var):
			vars.add(expr.varName)
			return vars

		#if (e is a Abs var exp)
		if isinstance(expr,Abs):
			free = FreeVars(expr.ch.exp, vars)
			free.remove(expr.ch.var.varName)#because it's bound by this abstraction
			#how would it be bound by the abstraction if it didnt actually appear in the body?
			#well, *if* it appears in the body then we remove it but i hope this
			#set routine already handles that
			return free
		#if (e is a App e1 e2)
		if isinstance(expr,App):
			free_e1 = FreeVars(e1, vars)
			free_e2 = FreeVars(e2, vars)
			return free_e1.union(free_e2)
#a var X appearing in an expression is free, 
#unless it is used in the .ch.exp of an abstraction
#whose .ch.var is that var, unless unless the expression
#is an application and X is free in the other half
#hrm good point, lemme see what the wiki says

#"The set of free variables of (a b) is the union of the set
#of free variables of a and the set of free variables of b"

lc2 = Dotdict() 
lc2._dict = odict()
def build_in_lc2(r):
	r["lc2"] = B.builtinmodule.inst_fresh()
	r["lc2"].ch.statements.items = [
		Comment("""simply typed lambda calculus""")]

	r["lc2-test"] = B.builtinmodule.inst_fresh()
	r["lc2-test"].special_scope = [r["lc2"], B.number];
		
	

	build_in(SyntacticCategory({'name': Text("exp")}), None, lc2)
	lc2.exp.help = ["a lambda expression"]
	

	class Var(Syntaxed):
		brackets = ("", "")
		help = ["a variable"]
		@property
		def varName(s):
			return s.ch.name.pyval
		@varName.setter
		def varName(s, v):
			s.ch.name.pyval = v
		
	build_in(SyntaxedNodecl(Var,
		[ChildTag("name")],
		{'name': B.restrictedidentifier}), None, lc2)

	class ParExp(Syntaxed): 
		help = ["a parenthesized expression"]
		brackets = ("", "")
		
	build_in(SyntaxedNodecl(ParExp,
		[TextTag("("), ChildTag("exp"), TextTag(")")],
		{'exp': lc2.exp}), None, lc2)
	build_in(WorksAs.b(lc2.parexp, lc2.exp), False, lc2)


	build_in(SyntacticCategory({'name': Text('type')}), None, lc2)

	class ParType(Syntaxed): 
		help = ["a parenthesized type"]
		brackets = ("", "")
	build_in(SyntaxedNodecl(ParType,
		[TextTag("("), ChildTag("type"), TextTag(")")],
		{'type': lc2.type}), None, lc2)
	build_in(WorksAs.b(lc2.partype, lc2.type), False, lc2)


	class FunType(Syntaxed): 
		help = ["function type"]
	build_in(SyntaxedNodecl(FunType,
		[
		[ChildTag("from"), TextTag("->"), ChildTag("to")],
		["function from ", ChildTag("from"), " to ", ChildTag("to")]],
		{'from': lc2.type, 'to': lc2.type}), None, lc2)
	build_in(WorksAs.b(lc2.funtype, lc2.type), False, lc2)


	#this, alright so we'll make syntax class for it
	class IntType(Syntaxed): 
		help = ["integer type"]
	build_in(SyntaxedNodecl(IntType,
		[TextTag("int")],
		{}), None, lc2)
	class BoolType(Syntaxed): 
		help = ["bool type"]
	build_in(SyntaxedNodecl(BoolType,
		[TextTag("bool")],
		{}), None, lc2)


	build_in(SyntacticCategory({'name': Text('basetype')}), None, lc2)
	build_in(WorksAs.b(lc2.basetype, lc2.type), False, lc2)
	build_in(WorksAs.b(lc2.booltype, lc2.basetype), False, lc2)
	build_in(WorksAs.b(lc2.inttype,  lc2.basetype), False, lc2)



	build_in(SyntacticCategory({'name': Text('constant')}), None, lc2)
	build_in(SyntacticCategory({'name': Text('bool')}), None, lc2)
	build_in(WorksAs.b(lc2.bool, lc2.constant), False, lc2)
	#and then i guess a line like this
	build_in(WorksAs.b(B.number,  lc2.constant), False, lc2)
	build_in(WorksAs.b(lc2.constant, lc2.exp), False, lc2)



	class BoolTrue(Syntaxed): 
		help = ["..."]
	build_in(SyntaxedNodecl(BoolTrue,
		[TextTag("true!")],
		{}), None, lc2)
	build_in(WorksAs.b(lc2.booltrue, lc2.bool), False, lc2)
	class BoolFalse(Syntaxed): 
		help = ["..."]
	build_in(SyntaxedNodecl(BoolFalse,
		[TextTag("false!")],
		{}), None, lc2)
	build_in(WorksAs.b(lc2.boolfalse, lc2.bool), False, lc2)




	"""
Type := FunType | BaseType
FunType := Type -> Type
BaseType := "Int" | "Bool"
Constant := Number | Bool

ParType := "(" Type ")"
Type := ParType
ParExpr := "(" Expr ")"

Expr := Var | Abs | App | Constant
Var := Identifier
Abs := "\\" Var ":" Type "." Expr
App := Expr " " Expr
	"""

	
	class Abs(Syntaxed): 
		help = ["abstraction, a lambda"]
		
	build_in(SyntaxedNodecl(Abs,
		[[TextTag("\\"), ChildTag("var"), TextTag(":"), ChildTag("type"), TextTag("."), ChildTag("exp")],
		[TextTag("function taking ("), ChildTag("var"), TextTag(" - a "), ChildTag("type"), TextTag("):"), IndentTag(),"\n",  ChildTag("exp"), DedentTag(), "\n"]],
		{'var': lc2.var, 'type': lc2.type, 'exp': lc2.exp}), None, lc2)



	#"do" <function> "to" <argument>
	#"run" <function> "on" <argument>
	class App(Syntaxed): 
		help = ["function application, a call"]
		
	build_in(SyntaxedNodecl(App,
		[[ChildTag("e1"), TextTag(" "), ChildTag("e2")],
		[ChildTag("e1"), TextTag(" applied to "), ChildTag("e2")]],
		{'e1': lc2.exp, 'e2': lc2.exp}), None, lc2)

	for x in [App, Abs, FunType]: x.default_syntax_index = 1

	build_in(WorksAs.b(lc2.app, lc2.exp), False, lc2)
	build_in(WorksAs.b(lc2.abs, lc2.exp), False, lc2)
	build_in(WorksAs.b(lc2.var, lc2.exp), False, lc2)


	r["lc2"].ch.statements.items.extend(list(itervalues(lc2._dict)))
	




	ParExp.unparen = lambda s: s.ch.exp.unparen()
	ParType.unparen = lambda s: s.ch.type.unparen()



	

	
	#//aka evaluate
	#//Normal order:
	def normalize (e) :
		if type(e) in [BoolTrue, BoolFalse, Number]:
			return e
		if isinstance(e, Var):
			#yea this isnt the top-level-only normalize()
			#print("Your type-checking sucks")
			#assert False
			return e
			
		if isinstance(e, Abs):
			#return Abs({'var': e.ch.var.copy(), e.ch.exp.eval()})
			return Abs({'var': e.ch.var, 'type': e.ch.type, 'exp': e.ch.exp.eval()})
			
		if isinstance(e, App):
			if isinstance(e.ch.e1, Abs):
				#//one-step evaluation:
				
				#return subst(e.ch.e1.ch.e2, e.ch.e1.ch.e1, e.ch.e2)
				#return subst(e.ch.e1.ch.exp, e.ch.e1.ch.var, e.ch.e2)
				
				#//full evaluation:
				#return subst(e3,x,e2).eval()
				return subst(e.ch.e1.ch.exp, e.ch.e1.ch.var, e.ch.e2).eval()
				
			if isinstance(e.ch.e1, App):
				#//one step eval or no-op
				#tmp = e.ch.e1.eval()
				#return App({'e1': tmp, 'e2' : e.ch.e2})
				
				#//definite one step evaluation:
				#not a no-op unless it's in normal form
				#tmp = e.ch.e1.eval()
				#if(tmp == e.ch.e1)
				#	return App({'e1': e.ch.e1, 'e2': e.ch.e2.eval()})
				#else
				#	return App({'e1': tmp, 'e2': e.ch.e2})
				
				
				#//full evaluation:
				tmp = e.ch.e1.eval()
				
				#only run subst if tmp is an Abs
				
				if isinstance(tmp, Abs):
					return subst(tmp.ch.exp,tmp.ch.var,e.ch.e2).eval()
				else:
					print("Your type-checking sucks")
					assert false
					#return App({'e1': tmp, 'e2': e.ch.e2.eval()})
					
			return e
		assert False, "normalize"


	def eval(e):
		x = e.copy().unparen()
		print (x.tostr())
		n = normalize(x)
		assert n
		return n.copy()

	ParExp.eval = App.eval = Abs.eval = Var.eval = eval



#?
	for x in [BoolTrue, BoolFalse]:
		x._eval = lambda s:s.copy()



	freshvarid = [0]
	def genFreshVarName():
		freshvarid[0] += 1
		return "var" + freshvarid[0]


	def subst( where, what:Var, by):#e1,x,e2):
		print ("subst where", where.tostr(), "what", what.tostr(), "by", by.tostr())
		if type(where) in [BoolTrue, BoolFalse, Number]:
			return where
		if isinstance(where, Var):
			#(Var x)[x := r]         = r
			if (where.varName == what.varName):
				return by
			#(Var y)[x := r]         = y 
			#i'm thinking more like this case
			else:
				return where
		if isinstance(where, App):
			#(App t s)[x := r]       = (t[x:=r])(s[x:=r])
			
			#right, what type?
			#types are irrelevant by the time we get to eval
			return App({'e1': subst(where.ch.e1, what, by), 'e2': subst(where.ch.e2, what, by)})
		if isinstance(where, Abs):
			#(Abs x t)[x := r]       = (Abs x t).
			#i think this should be where.ch.var.varName?
			#ah, yea
			# guess we never called an example that used it
			#name would be "RestrictedIdentifier" i think
			#i'm actually still a bit confused about this
			#case myself, but it's what the capture-avoiding
			#substitution rules say to do, *shrug*
			if(where.ch.var.varName == what.varName):
				print ("where is what so fuck you")
			#this would happen in a case like:
			#(\x.(\x.x)) y
			#to evaluate this we're gonna "replace all
			#occurences of 'x' in (\x.x) with 'y'"
			#but i guess the inner \x is taken to be
			# a different var than the outer \x
			
				return where
			else:
				#(Abs y t)[x := r]                                                                
				#if(y not in FreeVars(r))
				
				print("where.var:", where.ch.var.varName, "FreeVars(by):",FreeVars(by))
				if(where.ch.var.varName not in FreeVars(by)):
					print ("var not in freevars")
					#(Abs y subst(t,x,r))
					#i guess not completely irrelevant
					return Abs({'var':where.ch.var, 'type': where.ch.type, 'exp': subst(where.ch.exp, what, by)}) 
				else:
					print ("var in freevars")
					z = genFreshVarName()

					#t' = subst(t,y,z)
					t1 = subst(where.ch.exp,where.ch.var,z)

					#t'' = subst(t',x,r)
					t2 = subst(t1,what,by)

					#return (Abs z t'')
					return Abs({'var': z, 'type': where.ch.type, 'exp': t2})
		assert False, ("subst", where, what, by)
		
		
	
	def FreeVars(expr,vars=None) -> set:
		#shall we save varNames only?
		#we could do that, name is all the structure they have
		#otherwise this set magic wont work so magically
		#standard implementations would do something like
		#de bruijn indexes, i.e. just replace them with numbers

		if vars==None: vars = set()
		print("freevars", expr.tostr(), "vars:", vars)
		if type(expr) in [BoolTrue, BoolFalse, Number]:
			return vars
		if isinstance(expr,Var):
			vars.add(expr.varName)
			return vars

		#if (e is a Abs var exp)
		if isinstance(expr,Abs):
			free = FreeVars(expr.ch.exp, vars)
			free.remove(expr.ch.var.varName)#because it's bound by this abstraction
			#how would it be bound by the abstraction if it didnt actually appear in the body?
			#well, *if* it appears in the body then we remove it but i hope this
			#set routine already handles that
			return free
		#if (e is a App e1 e2)
		if isinstance(expr,App):
			free_e1 = FreeVars(e1, vars)
			free_e2 = FreeVars(e2, vars)
			return free_e1.union(free_e2)

		assert None, expr
#a var X appearing in an expression is free, 
#unless it is used in the .ch.exp of an abstraction
#whose .ch.var is that var, unless unless the expression
#is an application and X is free in the other half
#hrm good point, lemme see what the wiki says

#"The set of free variables of (a b) is the union of the set
#of free variables of a and the set of free variables of b"

	#so we call type_check with the expression
	#to be type-checked and a list of "type-assumptions"
	
	#for the top-level expression that we intend to
	#evaluate, we'll be calling this with the default,
	#i.e. an empty set of type-assumptions.
	
	#the set of type-assumptions is a map from vars
	#to their types
	def type_check(expr,env=None):
		if env==None: env = {}
		#so if our 'e' was a Var, then we're
		#just gonna grab it's type-assumption
		#from the list
		
		#if the type-assumption isn't there, then
		#we'll get a KeyError, which is fine cause
		#we're supposed to fail anyway in that case
		
		#if the type-assumption isn't there, then
		#it's basically like i just give you:
		
		# "x"
		#and ask you what's the type
		#there's no answer to that, it's untyped
		if isinstance(expr,Var):
			return env[expr.varName]
			"""
			check if expr is in env
			if so return the type associated
			with it, otherwise fail
			(if it's not there then python
			will fail for us, i hope)
		
			all vars must have a type-assumption
			by the time we get to them.
			type assumptions are given by abstractions,
			i.e. if we have '\\x:t.e', then when we go to
			type-check 'e', then env will contain 'x:t'
			"""
		#type-assumptions get added to the list from
		#abstractions
		
		#\\x:t.e, <-- "x:t" is a type-assumption
		#we'll add this type assumption to the list
		#before checking "e". 
		if isinstance(expr,Abs):
			#copy our current list of type-assumptions
			tmp_env = dict(env)
			
			#add the type assumption
			#if it's a repeated occurrence of a
			#var in an inner lambda like
			#\x:bool.\x:bool.x, then the inner
			#should shadow the outer
			
			#actually for a real lang we would
			#probably want to just disallow that
			#syntactically hrrm
			
			#\x:bool.\x:int.x
			#which x are we referring to?
			#the inner:p
			#our type-assumption will be the
			#inner one, that's ensured by this
			#next line, but how about for
			#normalization, substitution, etc?
			
			#so normalize doesnt deal with this as expected?
			#well, i think it's more that "expected" isnt
			#even really well-defined yet (for us)
			#well..lexical scope, i.e. the inner should
			#shadow the outer?yea ok we'll check over it in
			#a minute
			
			#it's not a big deal though, we
			#can just avoid those for now and
			#nit-pick at it later
			tmp_env[expr.ch.var.varName] = expr.ch.type
			return FunType({
				#this is just 't'
				"from": expr.ch.type,
				#\\x:t.e
				#so here we're type-checking the 'e'
				#using the new set of type-assumptions
				"to": type_check(expr.ch.exp,tmp_env)
				})
			#alright i think thats clear
			
		if isinstance(expr,App):
			func_t = type_check(expr.ch.e1, env)
			if isinstance(func_t,FunType):
				arg_t = type_check(expr.ch.e2, env)
				if arg_t.eq_by_value_and_python_class(func_t.ch._dict["from"]):
					return func_t.ch.to
				else:
					print("Bad argument type")
					assert False
			else:
				print("Application using non-function-type")
				assert False

		if type(expr) in [BoolTrue, BoolFalse]:
			return BoolType({})
		if isinstance(expr, Number):
			return IntType({})
		assert False
		#alright so, wanna show me what would be the lemonish way to handle this? 
		#welllllll
		#theres Number.decl i guess, 
		
		
	def tc(e):
		x = e.copy().unparen()
		print (x.tostr())
		n = type_check(x)
		assert n
		return n.copy()

		
	for x in [Var, App, Abs]:
		x.type_check = tc
		












"""
    	 _________________________
        / _____________________  /|
       / / ___________________/ / |
      / / /| |               / /  |
     / / / | |              / / . |
    / / /| | |             / / /| |
   / / / | | |            / / / | |
  / / /  | | |           / / /| | |
 / /_/__________________/ / / | | |
/________________________/ /  | | |
| ______________________ | |  | | |
| | |    | | |_________| | |__| | |
| | |    | |___________| | |____| |
| | |   / / ___________| | |_  / /
| | |  / / /           | | |/ / /
| | | / / /            | | | / /
| | |/ / /             | | |/ /
| | | / /              | | ' /
| | |/_/_______________| |  /
| |____________________| | /
|________________________|/

"""







cube = Dotdict() #a helper dict to hold the nodes being built in and to refe
cube._dict = odict()


def build_in_cube(r):
	r["cube"] = B.builtinmodule.inst_fresh()
	r["cube"].ch.statements.items = [
		Comment("""The lambda cube""")]

	r["cube-test"] = B.builtinmodule.inst_fresh()
	r["cube-test"].special_scope = [
		r["cube"]
		#B.number
	];
	
	build_in(SyntacticCategory({'name': Text("exp")}), None, cube)
	cube.exp.help = ["a lambda expression"]


	class Var(Syntaxed):
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
			#if s.varName in ["box", 'star']:
				#assert False, s.varName
			#alright for now we'll take this assert out just to make sure we'll make it to the
			#parse we want
			#well it will kill the whole thing 
			#well...this approach isnt good in that we will have multiple parses, and processing some of those will abort
			#well..gets the job done?
#if we should discuss how this should be handled in lemon eventually, i dont know,
#i think in some cases we want the ambiguity...is all i know, i mean eventually in some big lemon lang
#ah sure, in a more extensive lang we might want to allow ambiguity in some cases
#for this though the only reason we have any ambiguity is because we have things as
#text instead of haskell inductive data types
#ill think about it some more, for now let's just avoid using any ambiguous examples
	build_in(SyntaxedNodecl(Var,
		[ChildTag("name")],
		{'name': B.restrictedidentifier}), None, cube)
	class ParExp(Syntaxed):
		help = ["a parenthesized expression"]
		brackets = ("", "")
	
	build_in(SyntaxedNodecl(ParExp,
		[TextTag("("), ChildTag("exp"), TextTag(")")],
		{'exp': cube.exp}), None, cube)

	
	class PiType(Syntaxed):
		help = ["""function type
		
		is this equivalent to FunType? whats the var there for?
		yea this is the new function type, it's actually a 
		generalization of function types: it's *dependent* function
		types, meaning the return type can depend on the input
		*value*, meaning the return type can be given as an
		expression in terms of the input value (which is what the
		var is there for)
		\\x:t -> (x -> x)
		so (x -> x) is a type of an identity function?
		the identity function for type x happens to be of type x -> x
		but there are other functions besides the identity function
		which have this as their type
		any function that takes an x and returns an x is of type x -> x
		sure
		this takes args of type 't', calls them 'x', and
		for any arg 'x', returns a value of type 'x->x'
		't' as in a type variable?
		
		well, this was a bad example because the only way
		i could actually do something like this is if i used
		* instead of t
		
		\\t : * . (t -> t)
		
		^ because i have to know that my 't' is a type in order
		to use "->" to construct a function/pi-type with it
		like, for example, \\x : bool . (x -> x) doesn't make
		any sense
		
		\\(arg)x:(type)t -> (ret)(x -> x)?
		right, and (ret) itself is a PiType
		\\_:x -> x
		\\arg:type -> ret
		  ^ this is just pretending it's quantified over the terms in
		  the type x, using some var "_" that doesn't appear in the
		  return type
		so..ret is an expression...
		not just ret but also type
		
		x -> x?
		hrm actually that's not a good example because "->" requires
		two types to construct another type
		
		need an example that uses terms to construct types
		the identity type works, but we don't really have this represented
		yet
		
		\\x:t -> (x ==_t x)
		
		this one makes sense whatever we use for 't', but you'll have
		to use your imagination a bit because we don't have anything like
		identity types implemented
		
		in fact afaict we don't have anything implemented that can take
		terms as arguments and construct types
		
		"->" is a 'type operator', it takes two *types* as arguments and
		returns a type, you can't necessarily pass it two *terms* and
		have it construct a meaningful function type, like
		\\x:bool -> (x -> x) doesn't make sense but
		\\t:* -> (t -> t) does make sense
		
		==_t otoh can take two terms of type t and construct a type from
		them
		
		
		function type is recovered as a special case of these
		namely a standard function type is any pi-type where
		the expression representing the return type doesn't
		depend on the input value
		
		\\x:bool -> int
		this is a function that takes args of type 'bool', refers
		to them as 'x', and returns an 'int'
		
		this looks like ret holds the type,
		while the x'es look like ret holds ..i dunno what, a type of an expression that you evaluate to get the return type
		
		
		
		
		"int" is a constant, it's not an expression in terms
		of "x", so this is equivalent to the standard
		function type "bool -> int"
		
		\\x:* -> (x -> int)
		
		the return type "(x -> int)" is an expression in terms of x
		
		
		
		
		maybe we should move onto some example code?
		so 'type' is an expression but not just any expression..
		
		
	i was confused by expecting subtyping

		
so, we cant have a function taking an argument of any type and returning it,
we need to basically pass it the type too? yea
allowing ourselves to range over our types (i.e. t:*) for the input of
our function is polymorphism, and we use it here to get a polymorphic identity
function, and yea making our functions polymorphic like this is handled by
basically extending their definition to take a type and return the desired
function/type/expression

and why cant we do \\x:*.x?
^this looks like given a value return a value?
a value of type *, aka a value of type Type, aka a type
so the 'type' field in Pi is the return type?
the input type, same as the 'type' field in the Abs
to be proper about it, we'd call it "domain", because it's
quite literally the domain of any function of that function-type

\\arg : domain -> range

err
yeah i see what you mean here, but
\\x:_.x
what about this identity function?
we don't have anything to allow this syntax
we don't even have anything to allow this syntax:
\\_:x. <something>
well, _ is a valid identifier name
hrm
or what about \\x:y.x
cant this be a function that just ignores y?
this function has type y -> y

so, if we had the := syntax, i could write
identity := \\x:y.x
and it would typecheck?
well, our type_check() function (which is really more of a type-inferencer
than a type-checker) would return a valid type for this
i.e. y -> y
if you had like haskell syntax:

identity :: y -> y
identity := \\x:y.x

then yea the function definition would type-check against the function
declaration

and y would be..what?
i'm just assuming here that "y" is just short-hand we're
using to express some specific (but unsaid) type
well i was thinking it would be i guess a variable

so it would kinda be a type variable
in the simply typed lambda and beyond, we can't realy
use a variable except inside a function
this also holds for type variables

\\t : * . (\\x : t . x)

okay
so, the argument type of a function 


we can but that's saying something different
namely: given any type, return this type
rather than, given any type, and a value of that type, return that value

		
		
		
		
		"""]
	build_in(SyntaxedNodecl(PiType,
		[#look..a parenthesized expression cant subsume "type->ret", subsume?
		#you cant have <var>:<parenthetised expression> parse as a Pi
		#can we fix it so that we can?
		#im just guessing is this really the problem?
		#seems to be
		#we can break our examples but fix the problem by just adding the parentheses into
		#the TextTags here
		[ChildTag("arg"), TextTag(":"), ChildTag("type"), TextTag("->"), ChildTag("ret")],
		#["function from ", ChildTag("from"), " to ", ChildTag("to")]
		],
		#a parenthesized expression wouldn't work here?
		{'arg': cube.var, 'type': cube.exp, 'ret': cube.exp}), None, cube)
	
	class Abs(Syntaxed): 
		help = ["abstraction, a lambda"]
	build_in(SyntaxedNodecl(Abs,
		[[TextTag("\\"), ChildTag("var"), TextTag(":"), ChildTag("type"), TextTag("."), ChildTag("exp")],
		#[TextTag("function taking ("), ChildTag("var"), TextTag(" - a "), ChildTag("type"), TextTag("):"), IndentTag(),"\n",  ChildTag("exp"), DedentTag(), "\n"]
		],
		{'var': cube.var, 'type': cube.exp, 'exp': cube.exp}), None, cube)
	
	class App(Syntaxed): 
		help = ["""function application, a call
			#"do" <function> "to" <argument>
			#"run" <function> "on" <argument>
		"""]
		
	build_in(SyntaxedNodecl(App,
		[[ChildTag("e1"), TextTag(" "), ChildTag("e2")],
		#[ChildTag("e1"), TextTag(" applied to "), ChildTag("e2")]
		],
		{'e1': cube.exp, 'e2': cube.exp}), None, cube)
	
	
	class StarKind(Syntaxed):
		help = ["""star kind
		whats this?
		"""]
		def toStr(s):
			return "*"
			
	build_in(SyntaxedNodecl(StarKind,
		[TextTag("*")], #[TextTag("*")],
		{}), None, cube)
		
	class BoxKind(Syntaxed): 
		help = ["""box kind
		whats this?
		"""]
		def toStr(s):
			return "[]"
	build_in(SyntaxedNodecl(BoxKind,
		[TextTag("[]")], #[TextTag("[]")],
		{}), None, cube)
	
	build_in(SyntacticCategory({'name': Text("kind")}), None, cube)
	cube.kind.help = ["kind, like a type of types"]
	
	build_in(WorksAs.b(cube.starkind, cube.kind), False, cube)
	build_in(WorksAs.b(cube.boxkind, cube.kind), False, cube)
	
	
	
	#whoever came up with "pi", "box" and "star" must have had psychological problems
	#yes
	
	
	
	for a,b in [
	
	(cube.parexp, cube.exp),
	(cube.app, cube.exp), 
	(cube.abs, cube.exp), 
	(cube.var, cube.exp), 
	(cube.pitype, cube.exp),
	(cube.kind, cube.exp)
	
	]:build_in(WorksAs.b(a,b), False, cube)
	
	
	
	r["cube"].ch.statements.items.extend(list(itervalues(cube._dict)))
	
	
	#before theorem proving we probably want to type_check our prop and
	#make sure it type_checks to either * or [], then we won't have to
	#deal with the cases where our expression doesn't actually represent
	#a type/prop. (theorem proving is not applicable for anything except
	# propositions/types)
	
	#yes our proving process returns at most 1 result (but it should return
	#at least 1 result as long it has one!) we could fix this
	#with coroutines or some other inferencing process
	def prove(in_prop,env1=None,env2=None):
		if (env1 == None) : env1 = []
		if (env2 == None) : env2 = {}
		#if we had to pass this through type-checking then it would
		#fail cause it's a BoxKind, but we know it's a type, and
		#we know it's only term
		if isinstance(in_prop,BoxKind):
			yield StarKind({})#yep all these returns would just be yields instead
		#lol, yea something like that no really right hence the lol
		#so, then it resumes right here
		
		#i dunno, maybe we need some elifs instead of ifs?
		#just a bit i'm explaining to my bro
		
		elif (not type(type_check(in_prop,env2)) in [StarKind,BoxKind]):
			print("Can't prove something that's not a proposition/type")
			assert False
		
		#normalize it to reduce the number of different expression classes
		#we have to consider
		prop = nf(in_prop)
		
		#look up the prop in the 'env' 
		#if you find it, then return the associated bound variable
		#if you don't, then proceed to try the PiType case, where
		#we'll actually attempt to construct an Abs as our proof
		#term
		got_something = False
		for i in env1:
			if(betaEq(prop, i[0])):
				got_something = True
				yield i[1]
		
		if isinstance(prop,StarKind):
			print("Proving the proposition * is not yet implemented aside from in the case that it can be satisfied by the 'env' look-up.")
			#assert False 
		
		
		elif isinstance(prop,PiType):
			tmp_env1 = env1[:]
			tmp_env1.append([prop.ch.type,prop.ch.arg])
			tmp_env2 = dict(env2)
			tmp_env2[prop.ch.arg.varName] = prop.ch.type

			#so i guess this should really loop over the recursive call's results?
			for ppp in prove(prop.ch.ret,tmp_env1,tmp_env2):
				yield Abs({
					'var':prop.ch.arg, 
					'type': prop.ch.type, 
					'exp':  ppp
					})
				
		#we will get here as well
		#or we need to specify what case should fail
		
		#well i could hack this up but it would be better if you change the control flow appropriately instead
		elif not got_something:
			print ("What exactly are you telling me to prove here? " + prop.toStr())
			assert False
	
	def type_check(expr,env=None):
		#set up an empty list of type assumptions
		if (env == None) : env = {}
		
		#just like normally, we look up the type assumption for the variable
		#in the environment
		if isinstance(expr,Var):
			return env[expr.varName]	
	
		if isinstance(expr,App):
			#type-check-reduce the function using the current
			#environment
			func_t = whnf(type_check(expr.ch.e1,env))
			
			#functions are supposed to have pi-types. we only
			#allow functions to appear in function-position in
			#applications. so make sure it's type is a pi-type:
			if isinstance(func_t, PiType):
				#if so, type-check the argument expression
				#using the current environment
				arg_t = type_check(expr.ch.e2,env)
				
				#so, we're expecting that the type of the bound
				#variable in the function could potentially be
				#expressed by the application of a type operator
				#or dependent type
				
				#(\x:((\t:*.t->t) int).x) (\x:int.5)
				
				#func_t := ((\t:*.t->t) int) -> ((\t:*.t->t) int)
				#arg_t := int->int 
				if (not (betaEq(func_t.ch.type,arg_t))):
					print("Error: bad argument type")
					assert False
				
				else:
					return subst(func_t.ch.ret, func_t.ch.arg, expr.ch.e2)
			
			else:
				print("Error: trying to apply(call) something that's not a function")
				assert False
		
		if isinstance(expr,Abs):
			#make sure the type of the bound var passes a type-check
			#with the current environment. what does "pass" really
			#mean here?
			type_check(expr.ch.type,env)
			
			#copy the set of type assumptions into a new set
			tmp_env = dict(env)
			
			#add a type assumption for the bound variable to the
			#new set
			tmp_env[expr.ch.var.varName] = expr.ch.type
			
			#type-check the body of the abstraction using the new
			#set of type assumptions
			expr_t = type_check(expr.ch.exp,tmp_env)
			
			#abstractions have Pi-types as their types
			#so we're expecting the result of running type_check on
			#expr.ch.exp to be able to potentially return a type expression
			#that depends on 'expr.ch.var' ?
			
			rt = PiType({'arg':expr.ch.var,'type':expr.ch.type,'ret':expr_t})
			
			#now that we've constructed the pi-type for our lambda abstraction,
			#we're going to type-check the pi-type itself and make sure it
			#passes. what does "pass" really mean here?
			type_check(rt,env)
			
			#return the pi-type if it passes the type-check
			return rt
		
		if isinstance(expr,PiType):
			#type-check-reduce the input type
			s = whnf(type_check(expr.ch.type,env))
			
			#copy the set of type assumptions into a new set
			tmp_env = dict(env)
			
			#add a type assumption for the bound variable to
			#the new set
			tmp_env[expr.ch.arg.varName] = expr.ch.type
			
			#type-check-reduce the body of the abstraction
			#using the new set of type assumptions
			t = whnf(type_check(expr.ch.ret,tmp_env))
			
			
			#both s and t should be either * or []
			#at least if they're expected to *maybe* be
			#in "allowedKinds".
			
			#check if the particular combination is
			#allowed by the cube-configuration:
			#if not, fail type-checking. this is how
			#we control what corner what of the cube
			#we're using
			#print("PiType: (" + s.toStr() + ", " + t.toStr() + ")")
			if ( (s.__class__,t.__class__) not in allowedKinds):
				print ("Bad abstraction, AllowedKinds=", 
				[(x.__name__, y.__name__) for x,y in allowedKinds], ", argtype, bodytype = ", (s.__class__.__name__,t.__class__.__name__))
				assert False
			
			#the type of a pi-type is the type of it's body?
			#ok so.. i kind of have a feeling this is wrong
			#should be: return max(s,t)
			#when we switch over to MLTT universes, that's exactly what it will be
			#but i think that's what it's supposed to be here as well
			return t
		
		if isinstance(expr,StarKind):
			return BoxKind({}) 
		
		if isinstance(expr,BoxKind):
			print("Error: found a box")
			assert False
	
	allowedKinds = [(StarKind, StarKind), (StarKind, BoxKind), (BoxKind, StarKind), (BoxKind, BoxKind)]
	
	
	#The FreeVars function is still straight-forward
	#enough. What's less straight-forward to understand is
	#the mechanics of the language when the extra lambda
	#cube dependencies are added in.
	def FreeVars(expr, vars=None) -> set:
		if (vars == None): vars = set()
		
		#if the expression is a variable, add it
		#to the list of free variables. so what
		#happens to bound variables? they get removed
		#from the list in the abstraction case.
		if isinstance(expr,Var):
			vars.add(expr.varName)
			return vars
		
		#the free variables of an application is
		#the union of the free variables in each
		#of its components (function and argument)
		if isinstance(expr,App):
			free_e1 = FreeVars(expr.ch.e1,vars)
			return free_e1.union(FreeVars(expr.ch.e2,vars))
		
		#we don't care whether the variables are occurring
		#in an expression or its type, we just care where
		#variables are occurring, cause when we get into
		#the full lambda cube dependencies, things can be
		#going everywhere
		
		#the free variables of a typed abstraction is
		#the union of the free variables in it's input-type
		#component with the free variables in it's body
		#component, with the bound variable removed
		if isinstance(expr,Abs):
			free_t = FreeVars(expr.ch.type,vars)
			free_e = FreeVars(expr.ch.exp,vars)
			
			if(expr.ch.var.varName in free_e):
				free_e.remove(expr.ch.var.varName)
			return free_t.union(free_e)
		
		#the free variables of a pi-type is the union
		#of the free variables in it's input-type component
		#with the free variables in it's body component,
		#with the bound variable removed
		if isinstance(expr,PiType):
			free_t = FreeVars(expr.ch.type,vars)
			free_e = FreeVars(expr.ch.ret,vars)
			
			if(expr.ch.arg.varName in free_e):
				free_e.remove(expr.ch.arg.varName)
			return free_t.union(free_e)
		
		#the expressions "*" and "[]" don't contain
		#any variables, just return the current list of
		#free vars
		if type(expr) in [StarKind,BoxKind]:
			return vars
	
	
	
	#substitute "what" with "by" in "where"
	#he says his is is subst(what,where,by)
	#or                subst(v,   x,    e)
	#
	#but it's really   subst(what,by,where)
	def subst(where,what,by):
		#if the 'where' expression is the var that we're
		#substituting, then make the substitution, otherwise
		#just return 'where'.
		if isinstance(where,Var):
			if(where.varName == what.varName):
				return by
			else:
				return where
		
		#make the substitution into both the function and the argument
		#in an application
		if isinstance(where,App):
			return App({'e1':subst(where.ch.e1,what,by),'e2':subst(where.ch.e2,what,by)})
		
		
		
		if isinstance(where,Abs):
			#if the bound variable of the abstraction is the var
			#we're supposed to be substituting, then i guess we
			#say this new occurrence of a bound variable with the
			#same name shadows the substitution-variable in the
			#body expression. however, we still might be making the
			#substitution in the expression for the input-type of
			#the abstraction (i.e. dependent types & type operators)
			if(where.ch.var.varName == what.varName):
				return Abs({
					'var':where.ch.var.varName,
					'type':subst(where.ch.type,what,by),
					'exp':where.ch.exp
					})
			
			#else if the bound variable of the abstraction is in
			#the free variables of the 'by' expression, then 
			#replace the bound variable in the abstraction with a
			#fresh variable so that it won't interfere with the
			#free variables in 'by'. then substitute 'by' for 'what'
			#in both the input-type and the abstraction body
			elif (where.ch.var.varName in FreeVars(by)):
				z = genFreshVarName()
				t1 = subst(where.ch.exp,where.ch.var,z)
				return Abs({
					'var':z,
					'type':subst(where.ch.type,what,by),
					'exp':subst(t1,what,by)
					})
			
			#else we can just make the substitution directly since
			#there's no free-variable interference or scoping/shadowing
			#issues:
			else:
				return Abs({
					'var':where.ch.var,
					'type':subst(where.ch.type,what,by),
					'exp':subst(where.ch.exp,what,by)
					})
		
		#Pi's should work just like Abs
		if isinstance(where,PiType):
			if (where.ch.arg.varName == what.varName):
				return PiType({
					'arg':where.ch.arg,
					'type':subst(where.ch.type,what,by),
					'ret':where.ch.exp
					})
			
			elif (where.ch.arg.varName in FreeVars(by)):
				z = genFreshVarName()
				t1 = subst(where.ch.ret,where.ch.arg,z)
				return PiType({
					'arg':z,
					'type':subst(where.ch.type,what,by),
					'ret':subst(t1,what,by)
					})
			
			else:
				return PiType({
					'arg':where.ch.arg,
					'type':subst(where.ch.type,what,by),
					'ret':subst(where.ch.ret,what,by)
					})
		
		#* and [] both don't contain any vars so you're not gonna
		#substitute anything into them. return the expression as is.
		if type(where) in [StarKind,BoxKind]:
			return where
	
	#Alpha equivalence: check if the two expressions are
	#equivalent under variable renaming.
	def alphaEq(expr1,expr2):
		if (type(expr1) != type(expr2)): return False
		
		#ok, so this looks like it's explicitly *not* checking
		#if it's equivalent under renaming, since it's checking
		#if the names are equal.
		
		#this is accounted for by the rest of the function
		#when we encounter lambdas, we transform the 2nd expression
		#so that it's bound variable matches that of the 1st
		
		#that being said, i noticed some people in the comments
		#were pointing out small mistakes here and there, so once
		#we have it all down we might be on our own in ensuring that
		#it's 100% correct (not just this function but the whole thing)
		
		#what happens if it just gets two variables as the argument
		#expressions? no renaming happens so we'd fail alphaEq
		#in untyped lambda calculus we can have vars outside of
		#abstractions
		if (type(expr1) == Var):
			return (expr1.varName == expr2.varName)
		
		#App is simple enough, just check if both the functions
		#are alpha equivalent and if both the arguments are
		#alpha equivalent
		if (type(expr1) == App):
			return (alphaEq(expr1.ch.e1,expr2.ch.e1) 
				and alphaEq(expr1.ch.e2,expr2.ch.e2)
				)
		
		#Two abstractions with different bound variables can
		#mean the same thing, i.e. they would be the same
		#under a suitable variable renaming.
		
		#check if the input types are alpha equivalent, then
		#replace the bound variable in the second abstraction 
		#with the bound variable from the first lambda abstraction
		#and see if their bodies are syntactically equal
		
		#the syntactic equality is enforced by recursing down to the 
		#Var case above
		if (type(expr1) == Abs):
			return (alphaEq(expr1.ch.type,expr2.ch.type)
				and alphaEq(
					expr1.ch.exp,
					subst(expr2.ch.exp,expr2.ch.var,expr1.ch.var)
					)
				)
		
		#dependent function types
		#\x:t.x->x. 
		#not sure how to construct a type using terms.
		#
		#check if the input types are equal
		#replace the bound variable in the second pi-type
		#with the bound variable from the first and check
		#if their bodies are alpha-equivalent.
		if (type(expr1) == PiType):
			return (alphaEq(expr1.ch.type,expr2.ch.type)
				and alphaEq(
					expr1.ch.ret,
					subst(expr2.ch.ret,expr2.ch.arg,expr1.ch.arg)
					)
				)
		#there's only one * and there's only one [], and we know
		#by this point that the type()'s must be equal, so if
		#one of the expressions is * or [], then they both are,
		#and they're the same
		if (type(expr1) == StarKind):
			return True
		if (type(expr1) == BoxKind):
			return True
	
	
	
	#reduce both expressions to normal form and then check if they are
	#alpha-equivalent
	def betaEq(expr1,expr2):
		return alphaEq(nf(expr1),nf(expr2))
	
	
	
	#no idea wth is going on with nf() and whnf() here.
	#return the normal form of the expression
	#aka normalize()
	#aka evaluate()
	#aka beta-reduce()
	#... people should stop making new names for this thing
	#def nf(expr):
	#	return nf_spine(expr,[])
	
	#nf :: Expr -> Expr
	#nf ee = spine ee []
	#where spine (App f a) as = spine f (a:as)
	#spine (Lam s t e) [] = Lam s (nf t) (nf e)
	#spine (Lam s _ e) (a:as) = spine (subst s a e) as
	#spine (Pi s k t) as = app (Pi s (nf k) (nf t)) as
	#spine f as = app f as
	#app f as = foldl App f (map nf as)
	
	#dehaskellified
	def nf(expr):
		if type(expr) in [Var,StarKind,BoxKind]:
			return expr
		
		if isinstance(expr,App):
			nf1 = nf(expr.ch.e1)
			if isinstance(nf1,Abs):
				return nf(subst(nf1.ch.exp,nf1.ch.var,expr.ch.e2))
			
			else:
				print("What are you trying to normalize here?")
				assert False
		
		if isinstance(expr,Abs):
			return Abs({'var':expr.ch.var,'type':nf(expr.ch.type),'exp':nf(expr.ch.exp)})
		
		if isinstance(expr,PiType):
			return PiType({'arg':expr.ch.arg, 'type':nf(expr.ch.type),'ret':nf(expr.ch.ret)})
	
	
	
	
	
	
	#return the "weak head normal form" of the expression
	
	#whnf :: Expr -> Expr
	#whnf ee = spine ee []
	#where spine (App f a) as = spine f (a:as)
	#spine (Lam s e) (a:as) = spine (subst s a e) as
	#spine f as = foldl App f as
	
	def whnf(expr):
		#variables, abstractions, and pi-types are already in weak-head normal form
		#so just return them
		if type(expr) in [Var,Abs,PiType,StarKind,BoxKind]:
			return expr
		
		#if it's an application then we check whether there's an
		#application or an abstraction in the function position
		#(it shouldn't be anything else)
		if isinstance(expr,App):
			#if it's an abstraction in function position, then
			#we apply it to the argument. 
			#need to make sure the value we get as a result of this
			#is also in weak-head normal form.
			#i don't think he does this in "simpler, easier"
			if isinstance(expr.ch.e1,Abs):
				return whnf(subst(expr.ch.e1.ch.exp,expr.ch.var,expr.ch.e2))
			
			#if it's an application in function position, then
			#we whnf() that application and return a new application
			#that has this new expression as e1, but the same argument
			#for e2
			if isinstance(expr.ch.e1,App):
				return App({'e1':whnf(expr.ch.e1),'e2':expr.ch.e2})
			
			else:
				print("What are you trying to normalize here?")
				assert False
		
		else:
			print("What are you trying to normalize here?")
			assert False


	ParExp.unparen = lambda s: s.ch.exp.unparen()

	def eval(e):
		x = e.copy().unparen()
		#print (x.tostr())
		n = nf(x)
		assert n
		return n.copy()

	for x in [ParExp, App, Abs, Var, PiType, StarKind, BoxKind]: x._eval = eval
	for x in [ParExp, App, Abs, Var, PiType, StarKind, BoxKind]: x.type_check = type_check
	for x in [ParExp, App, Abs, Var, PiType, StarKind, BoxKind]: x.prove = prove


