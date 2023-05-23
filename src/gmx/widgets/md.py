import ipywidgets as w
from gmx.wrapper import GMX
import os
import re
import time
import mdtraj as md

class MD(w.VBox):
	def __init__(self,main):
		super().__init__(layout=w.Layout(**main.ldict))
		self.main = main

		self.nsec = w.FloatText(value=5.,description='Simulation length (ns)')
		self.startbutton = w.Button(description='Start')
		self.startbutton.on_click(self._start_click)
		self.stopbutton = w.Button(description='Stop',button_style='danger')
		self.stopbutton.on_click(self._stop)
		self.mdprog = w.FloatProgress(value=0.,min=0.,max=1.,description='Progress',orientation='horizontal')
		self.trload = w.Button(description='Reload trajectory')
		self.trload.on_click(self._trload)

		self.afbias = w.Checkbox(description='Alphafold',value=False)
		self.children = [ self.nsec, 
			w.HBox([w.Label('Add bias'), self.afbias ],layout=w.Layout(**main.ldict)),
			w.HBox([self.startbutton,self.stopbutton],layout=w.Layout(**main.ldict)),
			self.mdprog,
			self.trload
		]

		self.gmx = None
		self.phase = None

	def _start_click(self,e):
		self.soft_reset()
		self.main.status.start(self)

	def _merge_plumed(self):
		cwd = self.main.select.cwd()
		if self.afbias.value: # XXX or something else
			tr = md.load(f'{cwd}/npt.gro')
			natoms = tr.topology.select('protein').shape[0]
			plmd = [ f"WHOLEMOLECULES ENTITY0=1-{natoms}" ]
			
			metad = []
			if self.afbias.value:
				with open(f'{cwd}/af-plumed.dat') as f:
					plmd += [ l.rstrip() for l in f ]
				metad.append('afscore')


			# XXX: hardcoded 
			plmd += [
# XXX: AF going outside grid
#				f"metad: METAD ARG={','.join(metad)} PACE=1000 HEIGHT=1 BIASFACTOR=15 SIGMA={','.join(['0.1']*len(metad))} GRID_MIN={','.join(['-4']*len(metad))} GRID_MAX={','.join(['4']*len(metad))} FILE=HILLS",
				f"metad: METAD ARG={','.join(metad)} PACE=1000 HEIGHT=1 BIASFACTOR=15 SIGMA={','.join(['0.1']*len(metad))} FILE=HILLS",
				f"PRINT FILE=COLVAR ARG={','.join(metad)} STRIDE=100"
			]
	
			with open(f'{cwd}/plumed.dat','w') as p:
				p.write('\n'.join(plmd))
				p.write('\n')
				

	def status(self):
		cwd = self.main.select.cwd()
		if not self.gmx:
			with open("md.mdp.template") as t:
				mdp = t.readlines()
	
			self.nsteps = int(500 * 1000 * self.nsec.value) # XXX: hardcoded dt = 2fs
			mdp.append(f"nsteps = {self.nsteps}\n")

			with open(f"{self.main.select.cwd()}/md.mdp","w") as m:
				m.write("".join(mdp))

			try:
				self._merge_plumed()
			except Exception as e:
				self.main.msg.value = str(e)
				return 'error'
		
			self.gmx = GMX(workdir=cwd,pvc=self.main.pvc)
			self.gmx.start("grompp -f md.mdp -c npt.gro -t npt.cpt -p mol.top -o md.tpr")
			self.phase = 'grompp'
			yield 'starting','grompp',1

		while True:
			stat = self.gmx.cooked()
			if not stat:
				self.main.msg.value = 'Cannot read gromacs status'
				return 'error'

			if stat == 'done': 
				self.gmx.delete()
				if self.phase == 'mdrun':
					self.mdprog.value = 1.
					return 'idle'

				self.phase = 'mdrun'
				try:
					os.remove(f"{cwd}/md.log")
				except FileNotFoundError:
					pass
		
				if self.afbias.value:			# TODO or anything else
					plumed='-plumed plumed.dat'
				else:
					plumed=''
					
				self.gmx.start(f"mdrun -deffnm md -pin on -ntomp {self.main.cores} {plumed}",gpus=self.main.gpus,cores=(self.main.cores,.1))
				yield 'starting',self.phase,1

			elif stat == 'error':
				log = self.gmx.log()
				self.main.msg.value = log if log else 'Unknown gromacs errror'
				return 'error'
			elif stat == 'starting': yield 'starting',self.phase,2
			elif stat == 'running': 
				if self.phase == 'mdrun':
					s = 0.
					try:
						with open(f"{cwd}/md.log") as log:
							lines = log.readlines()
							for l in reversed(lines):
								if re.match('\s+Step\s+Time',l):
									s = float(re.match('\s+(\d+)\s+',prev).group(1))
									break
								prev = l
					except FileNotFoundError:
								pass
		
					self.mdprog.value = s / self.nsteps
					yield 'running',self.phase,5
				else:
					yield 'running',self.phase,1

	def _stop(self,e):
		if self.gmx:
			self.gmx.kill()

	def _trload(self,e):
	#	self.main.msg.value = ''
		self.trload.disabled = True
		odesc = self.trload.description
		self.trload.description = 'loading trajectory'
		pwd = self.main.select.cwd()
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


	def gather_status(self,stat):
		stat['md'] = {
			'nsec' : self.nsec.value,
			'mdprog' : self.mdprog.value,
			'afbias' : self.afbias.value,
		}
		if self.phase:
			stat['md']['phase'] = self.phase
		if self.gmx and self.gmx.name:
			stat['md']['gmx'] = self.gmx.name

	def restore_status(self,stat):
		self.nsec.value = stat['md']['nsec']
		self.nsteps = int(500 * 1000 * self.nsec.value)
		self.mdprog.value = stat['md']['mdprog']
		self.afbias.value = stat['md']['afbias']
		if 'gmx' in stat['md']:
			self.gmx = GMX(workdir=f'{self.main.select.cwd()}',pvc=self.main.pvc)
			self.gmx.name = stat['md']['gmx']
		if 'phase' in stat['md']:
			self.phase = stat['md']['phase']

	def reset_status(self):
		self.nsec.value = 5
		self.afbias.value = False
		self.soft_reset()

	def soft_reset(self):
		self.nsteps = int(500 * 1000 * self.nsec.value)
		self.mdprog.value = 0.
		self.gmx = None
		self.phase = None
