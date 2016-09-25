from nodes import *

def palette(s, scope, text, parser):
	"create menu items"
	if isinstance(s, CustomNodeDef):
		return [PaletteMenuItem(Ref(s)), PaletteMenuItem(NodeInstance(s))]
	elif isinstance(s, FunctionCallNodecl):
		#override NodeclBase palette() which returns a menuitem with a fresh() instance_class,
		#FunctionCall cant be instantiated without a target.
		return []
		#the stuff below is now performed in FunctionDefinitionBase
#		decls = [x for x in scope if isinstance(x, (FunctionDefinitionBase))]
#		return [PaletteMenuItem(FunctionCall(x)) for x in decls]
	elif isinstance(s, FunctionDefinitionBase):
		return [PaletteMenuItem(FunctionCall(s))]
	elif isinstance(s, Definition):
		return palette(s.ch.type, scope, text, None) + [PaletteMenuItem(Ref(s), 0)]
	elif isinstance(s, SyntacticCategory):
		return [PaletteMenuItem(Ref(s), 0)]
	elif isinstance(s, EnumType):
		r = [PaletteMenuItem(EnumVal(s, i)) for i in range(len(s.ch.options.items))] + [PaletteMenuItem(Ref(s))]
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
		return PaletteMenuItem(value, {'hardcoded regex-y match':score})
	elif isinstance(s, ExpNodecl):
		nodecls = [x for x in scope if isinstance(x, (NodeclBase))]
		return [PaletteMenuItem(Exp(x)) for x in nodecls]
	elif isinstance(s, VarRefNodecl):
		r = []
		for x in parser.vardecls_in_scope:
			assert isinstance(x, (UntypedVar, TypedParameter))
			r += [PaletteMenuItem(VarRef(x))]
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
	elif isinstance(s, NodeclBase):
		nodecls = [x for x in scope if isinstance(x, (NodeclBase))]
		return [PaletteMenuItem(Ref(x)) for x in nodecls]
	elif isinstance(s, NodeclBase):
		return PaletteMenuItem(s.instance_class.fresh())
	else:
		return []
