
# just for some type checking
class symbol_int(int):pass
class rule_int(int):pass

#some parser action callbacks

def ident(x):
	assert len(x) == 1
	return x[0]

def join(args):
	return ''.join(args)

def ignore(args):
	return None
