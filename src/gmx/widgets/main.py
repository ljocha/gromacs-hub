import ipywidgets as w
import os
import re

class Main(w.VBox):

	def __init__(self,**kwargs):
		super().__init__(**kwargs)
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
		children = [ self.select, self.status, self.view, self.ctrl, w.Label('Error output'), self.msg ]
		self.children = [ c for c in children if c is not None ]
