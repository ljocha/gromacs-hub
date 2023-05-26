import ipywidgets as w
import os
import re

class Main(w.VBox):

	def __init__(self,**kwargs):
		self.ldict = dict(width='100%', display='flex')
		super().__init__(**kwargs,layout=w.Layout(**self.ldict))
		self.select = None
		self.view = None
		self.status = None
		self.ctrl = None
		self.msg = None

		self.gpus = 1
		self.cores = 4

		# XXX
		mnt=os.popen('mount | grep /home/jovyan').read()
		pvcid=re.search('pvc-[0-9a-z-]+',mnt).group(0)
		self.pvc=os.popen(f'kubectl get pvc | grep {pvcid} | cut -f1 -d" "').read().rstrip()

	def build(self):
		children = [
			w.HTML('<h1>Gromacs+Plumed molecular dynamics with bias potential</h1>'),
			self.select,
			self.status, 
			w.HTML('<h3>Molecule / trajectory display</h3>'),
			self.view,
			w.HTML('<h3>Available actions</h3>Progress from left to right, in general.'),
			self.ctrl,
			w.HTML('<h3>Error output</h3>'),
			self.msg ]
		self.children = [ c for c in children if c is not None ]

	def gather_status(self,stat):
		for w in self.children:
			if hasattr(w.__class__,'gather_status'):
				w.gather_status(stat)

	def restore_status(self,stat):
		try:
			for w in self.children:
				if hasattr(w.__class__,'restore_status'):
					w.restore_status(stat)
		except Exception as e:
			self.msg.value = f'Status restore failed, resetting:\n{e}'
			self.reset_status()

	def reset_status(self):
		for w in self.children:
			if hasattr(w.__class__,'reset_status'):
				w.reset_status()
