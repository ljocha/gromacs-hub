import ipywidgets as w
from gmx.wrapper import GMX
import os
import re
import time
import mdtraj as md

class MD(w.VBox):
	def __init__(self,main):
		super().__init__()
		self.main = main

		self.nsec = w.FloatText(value=5.,description='Simulation length (ns)')
		self.startbutton = w.Button(description='Start')
		self.startbutton.on_click(lambda e: self.main.status.start('md',self))
		self.stopbutton = w.Button(description='Stop',button_style='danger')
		self.stopbutton.on_click(self._stop)
		self.mdprog = w.FloatProgress(value=0.,min=0.,max=1.,description='Progress',orientation='horizontal')
		self.trload = w.Button(description='Reload trajectory')
		self.trload.on_click(self._trload)
		self.children = [ self.nsec, w.HBox([self.startbutton,self.stopbutton]), self.mdprog, self.trload ]

		self.gmx = None

	def start(self,what):
		self.mdprog.value = 0.
		self.gmx = GMX(workdir=f'{self.main.select.cwd()}',pvc=self.main.pvc)

		with open("md.mdp.template") as t:
			mdp = t.readlines()

		self.nsteps = int(500 * 1000 * self.nsec.value) # XXX: hardcoded dt = 2fs
		mdp.append(f"nsteps = {self.nsteps}\n")

		with open(f"{self.main.select.cwd()}/md.mdp","w") as m:
			m.write("".join(mdp))
		
		self.gmx.start("grompp -f md.mdp -c npt.gro -t npt.cpt -p mol.top -o md.tpr")

	def started(self,what):
		stat = self.gmx.status()
		
		if not stat or stat.failed:
			log = self.gmx.log()
			self.main.msg.value = log
			self.gmx.delete()
			return 'error'

		else:
			if stat.active:
				self.watch = self._finished(what)
				return 'running'
			else:
				return  'starting'

	def finished(self,what):
		try:
			return next(self.watch)
		except StopIteration as e:
			return e.args[0]

	def _finished(self,what):
		while True:
			stat = self.gmx.status()
			if not stat or stat.failed:
				log = self.gmx.log()
				self.main.msg.value = log if log else 'job deleted'
				self.gmx.delete()
				return 'error',what

			if stat.succeeded:
				self.gmx.delete()
				break

			yield 'running',what

		try:
			os.remove(f"{self.main.select.cwd()}/md.log")
		except FileNotFoundError:
			pass

		self.gmx.start(f"mdrun -deffnm md -pin on -ntomp {self.main.cores}",gpus=self.main.gpus,cores=self.main.cores)

		while True:
			stat = self.gmx.status()
			if not stat or stat.failed:
				log = self.gmx.log()
				self.main.msg.value = log if log else 'job deleted'
				self.gmx.delete()
				return 'error',what

			if stat.succeeded:
				self.gmx.delete()
				return 'idle',None

			s = 0.
			try:
				with open(f"{self.main.select.cwd()}/md.log") as log:
					lines = log.readlines()
					for l in reversed(lines):
						if re.match('\s+Step\s+Time',l):
							s = float(re.match('\s+(\d+)\s+',prev).group(1))
							break
						prev = l
			except FileNotFoundError:
						pass

			self.mdprog.value = s / self.nsteps
			yield 'running',what


	def _stop(self,e):
		self.gmx.kill()
	

	def _trload(self,e):
	#	self.main.msg.value = ''
		self.trload.disabled = True
		odesc = self.trload.description
		self.trload.description = 'loading trajectory'
		gmx = GMX(workdir=f'{self.main.select.cwd()}',pvc=self.main.pvc)
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
	
		tr = md.load_xtc('pbc.xtc',top='mol.gro')
		idx=tr[0].top.select("name CA")
		tr.superpose(tr[0],atom_indices=idx)
		self.main.view.show_trajectory(tr)
		self.trload.description = odesc
		self.trload.disabled = False
