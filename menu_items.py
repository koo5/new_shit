
from __future__ import unicode_literals

from element import Element
import widgets
from tags import TextTag, WidgetTag

class MenuItem(Element):
	def __init__(self):
		super(MenuItem, self).__init__()
		#self.brackets = ('<','>')



class InfoItem(MenuItem):
	"""simple item with some stuff and a hide button"""
	def __init__(self, contents):
		super(InfoItem, self).__init__()
		if not isinstance(contents, list):
			contents = [contents]
		self.contents = contents
		self.color = "info item text"
		self.visibility_toggle = widgets.Toggle(self, True, ("(X)", "show"))
		self.visibility_toggle.color = self.visibility_toggle.brackets_color = "info item visibility toggle"

	def render(self):
		return self.contents + [TextTag("  "), WidgetTag("visibility_toggle")]

