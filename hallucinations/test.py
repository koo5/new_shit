from pyDatalog import pyDatalog


class Element(pyDatalog.Mixin):
	def __init__(self):
		super(Element, self).__init__()
		self.brackets_color = (200,0,0)
