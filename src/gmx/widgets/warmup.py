import ipywidgets as w

class Warmup(w.VBox):
	def __init__(self,main,**kwargs):
		super().__init__(**kwargs)
		self.main = main

		self.start = w.Button(description='Start')
		self.children = [ w.Label("TODO: params"), self.start ]
