
#todo: set up logging here?
#either inject @topic from lemon, or try/except import it here
#it should be then handled by a logging handler..


def try_loading_marpa():
	try:
		import cffi
		try:
			import marpa_cffi
			return True
		except cffi.VerificationError as e:
			return e
	except ImportError as e:
		return e


