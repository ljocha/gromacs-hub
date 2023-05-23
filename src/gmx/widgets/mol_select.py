import ipywidgets as w
import glob
import os
import json

class MolChooser(w.Dropdown):

	def __init__(self,main,**kwargs):
		super().__init__(description='Uploaded:')
		dirs = glob.glob('*.dir')
		self.options = [ d.replace('.dir','') for d in dirs ] + [ 'none' ]
		self.value = 'none'
		self.main = main
		self.observe(self._new_value,'value')

	def _new_value(self,e):
		self.main.status.stop_watch()
		self.main.view.show_pdb(self.value)
		if e.new != 'none':
			self.main.select.chosen = self.value
			try:
				with open(f'{self.main.select.cwd()}/status.json') as j:
					savestat = json.load(j)
				self.main.restore_status(savestat)
			except FileNotFoundError:
				self.main.reset_status()
			self.main.status.start_watch()
		else:
			self.main.select.chosen = None
			self.main.reset_status()

	def add_dir(self,base):
		# XXX
		if base not in self.options:
			self.options = sorted(list(self.options) + [base])

		self.value = base

class MolUpload(w.FileUpload):
	def __init__(self,main):
		super().__init__(accept = 'pdb',multiple = False,description='Upload new')
		self.main = main
		self.observe(self._uploaded,'_counter')

	def _uploaded(self,event):
		fname = list(self.value.keys())[0]
		base = fname.replace('.pdb','')
		try:
			os.mkdir(base + '.dir')
		except FileExistsError:			# XXX
			pass

		with open(f'{base}.dir/orig.pdb','wb') as f:
			f.write(list(self.value.values())[0]['content'])

		self.value.clear()
		self.main.select.chooser.add_dir(base)

		


class MolSelect(w.HBox):
	def __init__(self,main,**kwargs):
		super().__init__(**kwargs,layout=w.Layout(**main.ldict))
		self.main = main
		self.chooser = MolChooser(main)
		self.upload = MolUpload(main)
		self.children = [ self.chooser, w.Label('or'), self.upload ]
		self.chosen = None

	def cwd(self):
		if self.chosen:
			return self.chosen + '.dir'
		return None
