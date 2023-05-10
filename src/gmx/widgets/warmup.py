import ipywidgets as w

class Warmup(w.VBox):
	def __init__(self,chooser,**kwargs):
		super().__init__(**kwargs)
		self.chooser = chooser

		self.start = w.Button(description='Start')
		self.children = [ w.Label("TODO: params"), self.start ]
