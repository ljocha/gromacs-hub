import ipywidgets as w
import gmx.widgets as gw

class Ctrl(w.Tab):
	def __init__(self,main):
		super().__init__()
		self.main = main
		self.warmup = gw.Warmup(main)
		self.diag = gw.Diag(main)
		self.bias = w.Label('TODO')
		self.md = w.Label('TODO')
		self.children = [self.warmup, self.bias, self.md, self.diag]
		self.set_title(0,'Prepare molecule')
		self.set_title(1,'Bias potential')
		self.set_title(2,'Run MD')
		self.set_title(3,'Diagnostics')
