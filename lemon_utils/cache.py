class Cache(object):
	def __init__(s, generator):
		s.dirty = True
		s.generator = generator
		s.data = []

	def clear(s):
		s.dirty = False
		s.data = []
		s.iterator = s.generator()

	def fetch(s):
		i = s.iterator.__next__()
		s.data.append(i)
		return i

	def tryget(s, i):
		"""we dont implement __len__, it wouldnt make sense to fetch all available lines just to compare the final count with some number"""
		try:
			return s[i]
		except StopIteration as e:
			return None

	def __getitem__(s, i):
		#print ("__getitem__",i)
		while i >= len(s.data):
			s.fetch()
		return s.data[i]
