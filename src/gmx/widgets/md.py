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

		self.nsec = w.FloatText(value=5.,description='Length (ns)')
		self.startbutton = w.Button(description='Start')
		self.startbutton.on_click(self._start_click)
		self.stopbutton = w.Button(description='Stop',button_style='danger')
		self.stopbutton.on_click(self._stop)

		ml = main.ldict.copy()
		ml['width'] = '50%'

		self.mdprog = w.FloatProgress(value=0.,min=0.,max=1.,
			description='',orientation='horizontal',
			layout=w.Layout(**ml)
		)

		self.afbias = w.Checkbox(description='Alphafold',value=False)
		self.alpharmsd = w.Checkbox(description='Alpha RMSD',value=False)
		self.children = [ 
			w.HTML('<h4>Essential simulation parameters</h4>'),
			self.nsec, 
			w.HTML('<h4>Include bias potential(s) generated in the previous tab</h4>'),
			w.HBox([self.afbias, self.alpharmsd ],layout=w.Layout(**main.ldict)),
			w.HTML('<h4>Start simulation</h4>'),
			w.HBox([self.startbutton,self.stopbutton],layout=w.Layout(**main.ldict)),
			w.HTML('<h4>Progress</h4>'),
			self.mdprog,
		]

		self.gmx = None
		self.phase = None

	def _start_click(self,e):
		self.soft_reset()
		self.main.status.start(self)

	def _merge_plumed(self):
		cwd = self.main.select.cwd()
		if self.afbias.value or self.alpharmsd: # XXX or something else
			tr = md.load(f'{cwd}/npt.gro')
			natoms = tr.topology.select('protein').shape[0]
			plmd = f"""
WHOLEMOLECULES ENTITY0=1-{natoms}
MOLINFO STRUCTURE=mol.pdb
"""
			metad = []
			if self.afbias.value:
				plmd += self.main.ctrl.bias.af.dat.value
				metad.append('afscore')

			if self.alpharmsd:
				plmd += self.main.ctrl.bias.alpharmsd.dat.value
				metad.append('alpharmsd')

			# XXX: hardcoded 
			plmd += '\n'.join([
# XXX: AF going outside grid
#				f"metad: METAD ARG={','.join(metad)} PACE=1000 HEIGHT=1 BIASFACTOR=15 SIGMA={','.join(['0.1']*len(metad))} GRID_MIN={','.join(['-4']*len(metad))} GRID_MAX={','.join(['4']*len(metad))} FILE=HILLS",
				f"metad: METAD ARG={','.join(metad)} PACE=1000 HEIGHT=1 BIASFACTOR=15 SIGMA={','.join(['0.1']*len(metad))} FILE=HILLS",
				f"PRINT FILE=COLVAR ARG={','.join(metad)} STRIDE=100"
			])
	
			with open(f'{cwd}/plumed.dat','w') as p:
				p.write(plmd)
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

	def gather_status(self,stat):
		stat['md'] = {
			'nsec' : self.nsec.value,
			'mdprog' : self.mdprog.value,
			'afbias' : self.afbias.value,
			'alpharmsd' : self.alpharmsd.value,
		}
		if self.phase:
			stat['md']['phase'] = self.phase
		if self.gmx and self.gmx.name:
			stat['md']['gmx'] = self.gmx.name

	def restore_status(self,stat):
		try:
			self.nsec.value = stat['md']['nsec']
			self.nsteps = int(500 * 1000 * self.nsec.value)
			self.mdprog.value = stat['md']['mdprog']
			self.afbias.value = stat['md']['afbias']
			self.alpharmsd.value = stat['md']['alpharmsd']
			if 'gmx' in stat['md']:
				self.gmx = GMX(workdir=f'{self.main.select.cwd()}',pvc=self.main.pvc)
				self.gmx.name = stat['md']['gmx']
			if 'phase' in stat['md']:
				self.phase = stat['md']['phase']
		except KeyError:
			self.reset_status()
	
	def reset_status(self):
		self.nsec.value = 5
		self.afbias.value = False
		self.alpharmsd.value = False
		self.soft_reset()

	def soft_reset(self):
		self.nsteps = int(500 * 1000 * self.nsec.value)
		self.mdprog.value = 0.
		self.gmx = None
		self.phase = None
