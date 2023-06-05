import ipywidgets as w
import gmx.widgets as gw

class Bias(w.Tab):
	def __init__(self,main):
		super().__init__()
		self.main = main
		self.children = [ w.Label('blabla'), w.Label('hohoh') ]
		self.af = gw.AFBias(main)
		self.alpharmsd = gw.AlphaRMSD(main)
		self.children = [ self.af, self.alpharmsd ]
		self.set_title(0,'AlphaFold')
		self.set_title(1,'Alpha RMSD')

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
