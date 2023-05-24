import ipywidgets as w
import gmx.widgets as gw


class Ctrl(w.Tab):
	def __init__(self,main):
		super().__init__()
		self.main = main
		self.warmup = gw.Warmup(main)
		self.diag = gw.Diag(main)
		# self.bias = w.Tab([w.Label('TODO')])
		self.bias = gw.Bias(main)
		self.md = gw.MD(main)
		self.mdview = gw.MDView(main)
		self.children = [self.warmup, self.bias, self.md, self.mdview, self.diag]
		self.set_title(0,'Prepare molecule')
		self.set_title(1,'Bias potential')
		self.set_title(2,'Run MD')
		self.set_title(3,'Visualize MD')
		self.set_title(4,'Diagnostics')

		self.observe(self._tab_switch,'selected_index')

	def _tab_switch(self,e):
		if e.new == 3:
			self.main.view.clear()
		else:
			if e.old == 3:
				self.main.view.show_pdb(self.main.select.chosen)


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
