
import widgets
from nodes import *


class SetAllSyntaxesToZero(Syntaxed):
	def __init__(self):
		super(SetAllSyntaxesToZero, self).__init__()
		self.syntaxes = [[ch("widget")]]
		self.setw('widget', widgets.Button())
		self.widget.push_handlers(on_click = self.on_widget_click)
	def on_widget_click(self, widget):
		self.root.set_all_syntaxes_to_zero()

	@property
	def value(self):
		return self.widget.value

