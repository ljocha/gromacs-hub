import ipywidgets as w
import nglview as nv

class MolView(w.HBox):
	def __init__(self,main,**kwargs):
		super().__init__(**kwargs)

		self.main = main
		self.v = nv.NGLWidget()
		self.component = None
		self.licorice = w.Checkbox(description='Licorice',value=False)
		self.cartoon = w.Checkbox(description='Cartoon',value=True)
		self.children = [ 
			self.v,
			w.VBox([
				self.licorice,
				self.cartoon
			])
		]
