
#todo: set up logging here?

def try_loading_marpa():
	import cffi
	try:
		import marpa_cffi
		return True
	except cffi.VerificationError as e:
		return e


