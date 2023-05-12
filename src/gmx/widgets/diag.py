import ipywidgets as w
import os

class Diag(w.VBox):
	def __init__(self,main):
		super().__init__()
		self.main = main
	
		self.jobrefresh = w.Button(description='Refresh list')
		self.jobrefresh.on_click(self._listjobs)
		self.jobchoose = w.Dropdown()
		self.jobchoose.observe(self._choosejob,'value')
		self.jobout = w.Textarea(layout = w.Layout(width='90%',height='20ex'))
		self.purge = w.Button(description='Purge gmx jobs',button_style='danger')
		self.purge.on_click(self._purgejobs)
		self.dirls = w.Button(description='Refresh')
		self.dirls.on_click(self._dirls)
		self.dir = w.Textarea(layout = w.Layout(width='90%',height='20ex'))
		self.dirls = w.Button(description='Refresh')
		self.dirls.on_click(self._dirls)
		self.dir = w.Textarea(layout = w.Layout(width='90%',height='20ex'))
		self.purgedir = w.Button(description='Purge backup files',button_style='danger')
		self.purgedir.on_click(self._purgedir)

		self.children = [
			w.Label('Choose job'),
			w.HBox([ self.jobrefresh, self.jobchoose ]),
			w.Label('Job output'),
			self.jobout,
			self.purge,
			w.Label('Working directory'),
			self.dirls,
			self.dir,
			self.purgedir
		]

	def _listjobs(self,e):
		with os.popen("kubectl get pods | grep gmx-") as f:
			self.jobchoose.options = [ " ".join(p.rstrip().split()[::2]) for p in f ]

	def _purgejobs(self,e):
		with os.popen("kubectl get pods | grep gmx-") as f:
			pods = [ "pod/"+l.split()[0] for l in f ]
			os.system(f"kubectl delete {' '.join(pods)} >/dev/null")
		with os.popen("kubectl get jobs | grep gmx-") as f:
			pods = [ "job/"+l.split()[0] for l in f ]
			os.system(f"kubectl delete {' '.join(pods)} >/dev/null")

	def _choosejob(self,e):
		if e.new is not None:
			pod = e.new.split()[0]
			with os.popen(f"kubectl logs pod/{pod}") as f:
				self.jobout.value = "".join(f)

	def _dirls(self,e):
		with os.popen(f"ls -lt {self.main.select.cwd()}") as f:
			self.dir.value = "".join(f)


	def _purgedir(self,e):
		os.system(f"rm {self.main.select.cwd()}/\#*\#")
		self._dirls(None)
