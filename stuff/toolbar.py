
import widgets
from nodes import *


class SetAllSyntaxesToZero(Syntaxed):
	
	def __init__(self):
		super(SetAllSyntaxesToZero, self).__init__()
		self.syntaxes = [[t("set all syntaxes to zero here!"), w("widget")],
						 [t("normalize all syntaxes...but how...without a button?")],
						 [w("widget"), w("widget"), w("widget")],
 						 [t("normalizing all syntaxes removes any ambiguity from your programs")],
 						 [t("syntaxes shouldn't be abused like this anyway")],
						 [t("""this one is just for gremble""")],						 
						 ]
		self.widget = widgets.Button(self, "do it!")
		self.widget.push_handlers(on_click = self.on_widget_click)
	def on_widget_click(self, widget):
		self.root.set_all_syntaxes_to_zero()

	@property
	def value(self):
		return self.widget.value

