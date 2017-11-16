


def try_loading_marpa():
	try:
		import cffi
		try:
			import marpa_cffi.marpa_cffi
			return True
		except cffi.VerificationError as e:
			return e
	except ImportError as e:
		return e


