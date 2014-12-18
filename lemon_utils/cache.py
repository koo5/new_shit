
class Cache(object):
		def __init__(s, generator):
				s.dirty = True
				s.generator = generator
				s.data = []

		def get(s):
				if s.dirty:
						s.data.clear()
						return s.cache_and_yield()
				else:
						return s.data

		def cache_and_yield(s):
				s.dirty = False
				for item in s.generator():
						s.data.append(item)
						yield item

		def __len__(s):
			return len(s.data)

		def __getitem__(s, item):
			return s.data[item]