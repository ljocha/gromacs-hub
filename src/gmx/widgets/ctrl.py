import ipywidgets as w
import gmx.widgets as gw

class Ctrl(w.Tab):
	def __init__(self,main):
		super().__init__()
		self.main = main
		self.warmup = gw.Warmup(main)
		self.diag = gw.Diag(main)
		self.bias = w.Label('TODO')
		self.md = gw.MD(main)
		self.children = [self.warmup, self.bias, self.md, self.diag]
		self.set_title(0,'Prepare molecule')
		self.set_title(1,'Bias potential')
		self.set_title(2,'Run MD')
		self.set_title(3,'Diagnostics')

	def gather_status(self,stat):
		for w in self.children:
			if hasattr(w.__class__,'gather_status'):
				w.gather_status(stat)

	def restore_status(self,stat):
		for w in self.children:
			if hasattr(w.__class__,'restore_status'):
				w.restore_status(stat)

	def reset_status(self):
		for w in self.children:
			if hasattr(w.__class__,'reset_status'):
				w.reset_status()
