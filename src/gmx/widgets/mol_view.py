import ipywidgets as w
import nglview as nv

class MolView(w.HBox):
	def __init__(self,main,**kwargs):
		super().__init__(**kwargs)

		self.main = main
		self.v = nv.NGLWidget()
		self.v.layout.width = '70%'
		self.v.handle_resize()
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

		self.licorice.observe(self._change_representation,'value')
		self.cartoon.observe(self._change_representation,'value')

	def _change_representation(self,e):
		self.v.clear()
		if self.licorice.value:
			self.v.add_licorice()
		if self.cartoon.value:
			self.v.add_cartoon(color='residueindex')

	def show_pdb(self,base):
		if self.component:
			self.v.remove_component(self.component)
			self.component = None

		self.v.clear()
		try:
			self.component = self.v.add_component(f'{base}.dir/orig.pdb')
			self.licorice.value = False
			self.cartoon.value = True
		except Exception: # XXX
			pass

	def show_trajectory(self,tr):
		if self.component:
			self.v.remove_component(self.component)
			self.component = None

		self.v.clear()
		self.component = self.v.add_trajectory(tr)
		self.licorice.value = False
		self.cartoon.value = True
			
