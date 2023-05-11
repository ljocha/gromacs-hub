import ipywidgets as w

class Warmup(w.VBox):
	def __init__(self,main,**kwargs):
		super().__init__(**kwargs)
		self.main = main

		self.startbutton = w.Button(description='Start')
		self.children = [ w.Label("TODO: params"), self.startbutton ]


		self.startbutton.on_click(lambda e: self.main.status.start('warmup',self))


	def start(self,what):
		pass

	def started(self):
		return True

	def finished(self):
		return 'idle',None
