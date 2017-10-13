from nodes import *

def tb():
	return "hi"
	import traceback
	return (traceback.extract_stack())

def palette(s, scope, text, parser):
	"create menu items"
	if isinstance(s, CompoundNodeDef):
		return [PaletteMenuItem(tb(), Ref(s)), PaletteMenuItem(tb(), CompoundNode(s))]
	elif isinstance(s, FunctionCallNodecl):
		decls = [x for x in scope if isinstance(x, (FunctionDefinitionBase))]
		return [PaletteMenuItem(tb(), FunctionCall(x)) for x in decls]
	#elif isinstance(s, FunctionDefinitionBase):
	#	return [PaletteMenuItem(tb(), FunctionCall(s))]
	elif isinstance(s, Definition):
		return palette(s.ch.type, scope, text, None) + [PaletteMenuItem(tb(), Ref(s), 0)]
	elif isinstance(s, SyntacticCategory):
		return [PaletteMenuItem(tb(), Ref(s), 0)]
	elif isinstance(s, EnumType):
		r = [PaletteMenuItem(tb(), EnumVal(s, i)) for i in range(len(s.ch.options.items))] + [PaletteMenuItem(tb(), Ref(s))]
		return r
	elif isinstance(s, Nodecl):
		i = s.instance_class
		m = i.match(text)
		if m:
			value = i(text)
			score = 300
		else:
			value = i()
			score = 0
		return [PaletteMenuItem(tb(), value, {'hardcoded regex-y match':score})]
	elif isinstance(s, ExpNodecl):
		nodecls = [x for x in scope if isinstance(x, (NodeclBase))]
		return [PaletteMenuItem(tb(), Exp(x)) for x in nodecls]
	elif isinstance(s, VarRefNodecl):
		r = []
		for x in parser.vardecls_in_scope:
			assert isinstance(x, (UntypedVar, TypedParameter))
			r += [PaletteMenuItem(tb(), VarRef(x))]
		return r
		"""
				r = []
				for x in scope:
					xc=x.compiled
					for y in x.vardecls:
						yc=y.compiled
						#log("vardecl compiles to: "+str(yc))
						if isinstance(yc, (UntypedVar, TypedParameter)):
							#log("vardecl:"+str(yc))
							r += [PaletteMenuItem(VarRef(yc))]
				#log (str(scope)+"varrefs:"+str(r))
				return r
		"""
	elif isinstance(s, TypeNodecl):
		nodecls = [x for x in scope if isinstance(x, (NodeclBase))]
		return [PaletteMenuItem(tb(), Ref(x)) for x in nodecls]
	elif isinstance(s, NodeclBase):
		return [PaletteMenuItem(tb(), s.instance_class.fresh())]
#	elif isinstance(s, MycroftNodecl):
#		return [PaletteMenuItem(tb(), s.instance_class.fresh(cmd)) for cmd in mycroft.complete(text)]
	else:
		return []
