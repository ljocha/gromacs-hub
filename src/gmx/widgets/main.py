import ipywidgets as w

class Main(w.VBox):

	def __init__(self,**kwargs):
		super().__init__(**kwargs)
		self.select = None
		self.view = None
		self.status = None
		self.ctrl = None

	def build(self):
		children = [ self.select, self.status, self.view, self.ctrl ]
		self.children = [ c for c in children if c is not None ]
