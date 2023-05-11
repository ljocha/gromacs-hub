import ipywidgets as w
import os

class Diag(w.VBox):
	def __init__(self,main):
		super().__init__()
		self.main = main
	
		self.jobrefresh = w.Button(description='Refresh list')
		self.jobrefresh.on_click(lambda e: self._listjobs(e))
		self.jobchoose = w.Dropdown()
		self.jobchoose.observe(lambda e: self._choosejob(e),'value')
		self.jobout = w.Textarea(layout = w.Layout(width='90%',height='20ex'))
		self.children = [
			w.Label('Choose job'),
			w.HBox([ self.jobrefresh, self.jobchoose ]),
			w.Label('Job output'),
			self.jobout
		]

	def _listjobs(self,e):
		with os.popen("kubectl get pods | grep gmx-") as f:
			self.jobchoose.options = [ " ".join(p.rstrip().split()[::2]) for p in f ]

	def _choosejob(self,e):
		pod = e.new.split()[0]
		with os.popen(f"kubectl logs pod/{pod}") as f:
			self.jobout.value = "".join(f)

