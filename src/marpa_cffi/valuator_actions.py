# coding=utf-8
#some parser action ("valuator") callbacks

def ident(x):
	assert len(x) == 1
	return x[0]

def ident_list(x):
	return x

def join(args):
	return ''.join(args)

def ignore(args):
	return None
