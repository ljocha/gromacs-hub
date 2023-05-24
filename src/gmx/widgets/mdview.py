import ipywidgets as w
from gmx.wrapper import GMX
import os
import re
import time
import mdtraj as md
import plotly.graph_objects as go
import numpy as np

class MDView(w.VBox):
	def __init__(self,main):
		super().__init__(layout=w.Layout(**main.ldict))

		self.main = main
		self.trload = w.Button(description='Reload trajectory')
		self.trload.on_click(self._trload)

		self.frame = w.IntSlider(description='Frame',min=0,max=1)
		
		self.timeline = go.FigureWidget(
			data=[
				go.Scatter(x=[0], y=[1],
					 marker=go.scatter.Marker(line=dict(width=5),symbol=100,size=15,color='red')
				),
				go.Scatter(x=np.arange(100),y=np.zeros(100),
					 marker=go.scatter.Marker(color='blue')
				)
			],
			layout=go.Layout(height=500)
		)

		self.children = [ self.trload, self.frame, self.timeline ]
		w.link((self.frame,'value'), (main.view.v,'frame'))
		self.frame.observe(self._frame,'value')

	def _frame(self,e):
		with self.timeline.batch_update():
			self.timeline.data[0].x = [e.new]
			l = len(self.timeline.data[1].y)
			self.timeline.data[0].y = [ self.timeline.data[1].y[e.new if e.new < l else l-1] ]

		self.main.view.v.show()
		
	def _trload(self,e):
	#	self.main.msg.value = ''
		self.trload.disabled = True
		odesc = self.trload.description
		self.trload.description = 'loading trajectory'
		pwd = self.main.select.cwd()
		if os.path.getmtime(f'{pwd}/pbc.xtc') < os.path.getmtime(f'{pwd}/md.xtc'):
			gmx = GMX(workdir=pwd,pvc=self.main.pvc)
			gmx.start("trjconv -f md.xtc -s npt.gro -pbc nojump -o pbc.xtc",input=1)
			while True:
				stat = gmx.status()
				if stat.succeeded:
					gmx.delete()
					break
				if stat.failed:
					self.main.msg.value = gmx.log()
					self.trload.description = odesc
					self.trload.disablded = False
					gmx.delete()
					return
				time.sleep(2)
		
		tr = md.load_xtc(f'{pwd}/pbc.xtc',top=f'{pwd}/mol.gro')
		idx=tr[0].top.select("name CA")
		tr.superpose(tr[0],atom_indices=idx)
		self.main.view.show_trajectory(tr)
		self.trload.description = odesc
		self.trload.disabled = False
		self.frame.max = len(tr)

		rmsd = md.rmsd(tr,tr)
		rg = md.compute_rg(tr)
		with self.timeline.batch_update():
			self.timeline.data[1].x = np.arange(len(rmsd))
			self.timeline.data[1].y = rmsd


