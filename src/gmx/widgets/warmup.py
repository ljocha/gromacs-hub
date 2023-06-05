import ipywidgets as w
from gmx.wrapper import GMX
import os
import re

class Warmup(w.VBox):
	def __init__(self,main,**kwargs):
		super().__init__(**kwargs,layout=w.Layout(**main.ldict))
		self.main = main
		self.gmx = None
		self.phase = None
		self.mdpp = None

		self.startbutton = w.Button(description='Start')

		mdbox = 2.0
		self.simple_cmds = {
			"pdb2gmx": "pdb2gmx -f orig.pdb -o mol.gro -p mol.top -water tip3p -ff amber94 -ignh",
			"gro2pdb": "pdb2gmx -f mol.gro -o mol.pdb -p shit.top -water tip3p -ff amber94",
			"editconf": f"editconf -f mol.gro -o box.gro -c -d {mdbox} -bt dodecahedron",
			"solvate": "solvate -cp box.gro -cs spc216.gro -o solv.gro -p mol.top",
			"grompp-ions": "grompp -f ../ions.mdp -c solv.gro -p mol.top -o ions.tpr",
			"genion": ("genion -s ions.tpr -o ions.gro -p mol.top -pname NA -nname CL -neutral","13"),
		}

		self.mdruns = {
			"minimize" : (
				"grompp -f ../minim-sol.mdp -c ions.gro -p mol.top -o em.tpr",
				"mdrun -v -deffnm em -pin on",
				"em.log", 1000	# XXX: same as .mdp
				),
			"nvt" : (
				"grompp -f ../nvt.mdp -c em.gro -r em.gro -p mol.top -o nvt.tpr",
				"mdrun -v -deffnm nvt -pin on",
				"nvt.log", 50000
			),
			"npt" : (
				"grompp -f ../npt.mdp -c nvt.gro -r nvt.gro -t nvt.cpt -p mol.top -o npt.tpr",
				"mdrun -v -deffnm npt -pin on",
				"npt.log", 50000
			)
		}

		self.initprep = { k : w.Checkbox(description=k,value=False,disabled=True) for k in self.simple_cmds.keys() }
		self.mdprog = { k : w.FloatProgress(value=0., min=0., max=1., description=k, orientation='horizontal') for k in self.mdruns.keys() }

		self.children = [
			w.HTML('''Perform preparation of the molecule for MD in a batch -- 
apply force field, solvate, add counterions, minimize, 
run short isothermal-isochoric and isothermal-isobaric constrained simulations'''),
			w.Label("TODO: params"),
			self.startbutton,
			w.HTML('<h4>Progress</h4>'),
			w.HBox([
				w.VBox([w.Label('Initial steps')] + list(self.initprep.values()),layout=w.Layout(**main.ldict)),
				w.VBox([w.Label('Short simulations')] + list(self.mdprog.values()),layout=w.Layout(**main.ldict))],
				layout=w.Layout(**main.ldict)
			)
		]

		self.startbutton.on_click(self._start_click)

	def _start_click(self,e):
		self.reset_status()
		self.main.status.start(self)

	def _phases(self,start):
		if start in self.simple_cmds:
			i = list(self.simple_cmds.keys()).index(start)+1
			for k in list(self.simple_cmds.keys())[i:]:
				yield k,None

		i = 0
		if start in self.mdruns:
			i = list(self.mdruns.keys()).index(start)+1
		for k in list(self.mdruns.keys())[i:]:
			yield k,True
			yield k,False

		return

	def status(self):
		cwd = self.main.select.cwd()

		if not self.gmx:
			self.gmx = GMX(workdir=cwd,pvc=self.main.pvc)

		if self.phase is None: 
			self.phase = 'pdb2gmx'
			self.gmx.start(self.simple_cmds['pdb2gmx'])

		phases = self._phases(self.phase)

		while True:
			stat = self.gmx.cooked()
			if not stat:
				self.main.msg.value = 'Cannot read gromacs status'
				return 'error'

			if stat == 'done':
				self.gmx.delete()

				if self.phase in self.simple_cmds:
					self.initprep[self.phase].value = True
				elif not self.mdpp:
					self.mdprog[self.phase].value = 1.

				try:
					self.phase,self.mdpp = next(phases)
				except StopIteration:
					return 'idle'

				if self.phase in self.simple_cmds:
					if isinstance(self.simple_cmds[self.phase],tuple):
						self.gmx.start(self.simple_cmds[self.phase][0],input=self.simple_cmds[self.phase][1])
					else:
						self.gmx.start(self.simple_cmds[self.phase])
					yield 'starting',self.phase,2

				elif self.phase in self.mdruns:
					if self.mdpp:
						self.gmx.start(self.mdruns[self.phase][0])
						yield 'starting',self.phase+'-grompp',2
					else:
						try:
							os.remove(f"{cwd}/{self.mdruns[self.phase][2]}")
						except FileNotFoundError:
							pass
						self.gmx.start(self.mdruns[self.phase][1],gpus=self.main.gpus)
						yield 'starting',self.phase+'-mdrun',2
						
			elif stat == 'error':
				log = self.gmx.log()
				self.main.msg.value = log if log else 'Unknown gromacs error'
				return 'error'
			elif stat == 'starting': 
				suff = ''
				if self.mdpp is not None:
					suff = '-grompp' if self.mdpp else '-mdrun'
				yield 'starting',self.phase+suff,2
			elif stat == 'running':
				if self.mdpp is None:
					yield 'running',self.phase,1
				elif self.mdpp:
					yield 'running',self.phase+'-grompp',1
				else:
					s = 0.
					try:
						with open(f"{cwd}/{self.mdruns[self.phase][2]}") as log:
							lines = log.readlines()
							for l in reversed(lines):
								if re.match('\s+Step\s+Time',l):
									s = float(re.match('\s+(\d+)\s+',prev).group(1))
									break
								prev = l
					except FileNotFoundError:
						pass
	
					self.mdprog[self.phase].value = s / self.mdruns[self.phase][3]
					yield 'running',self.phase+'-mdrun',5
		


	def gather_status(self,stat):
		mystat = dict()

		if self.gmx and self.gmx.name:
			mystat['gmx'] = self.gmx.name

		for k in self.simple_cmds.keys():
			mystat[k] = self.initprep[k].value

		for k in self.mdruns.keys():
			mystat[k] = self.mdprog[k].value

		if self.phase is not None: mystat['phase'] = self.phase
		if self.mdpp is not None: mystat['mdpp'] = self.mdpp
		stat['warmup'] = mystat

	def restore_status(self,stat):
		mystat = stat['warmup']
		if 'gmx' in mystat:
			self.gmx = GMX(workdir=f'{self.main.select.cwd()}',pvc=self.main.pvc)
			self.gmx.name = mystat['gmx']
		
		for k in self.simple_cmds.keys():
			self.initprep[k].value = mystat[k]

		for k in self.mdruns.keys():
			self.mdprog[k].value = mystat[k] 
	
		self.phase = mystat['phase'] if 'phase' in mystat else None
		self.mdpp = mystat['mdpp'] if 'mdpp' in mystat else None

	def reset_status(self):
		self.gmx = None
		self.phase = None
		self.mdpp = None
		
		for k in self.simple_cmds.keys():
			self.initprep[k].value = False

		for k in self.mdruns.keys():
			self.mdprog[k].value = 0.
