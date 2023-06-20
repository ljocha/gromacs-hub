import ipywidgets as w
from gmx.wrapper import GMX
import os
import re

mdprscale = 4.

class Warmup(w.VBox):
	def __init__(self,main,**kwargs):
		super().__init__(**kwargs,layout=w.Layout(**main.ldict))
		self.main = main
		self.gmx = None
		self.mdbox = w.FloatText(value=2.0)

		ml = main.ldict.copy()
		ml['width'] = '50%'
		self.progress = w.FloatProgress(value=0.,min=0.,max=5.+3*mdprscale,orientation='horizontal',layout=w.Layout(**ml))

		self.startbutton = w.Button(description='Start')

#		self.initprep = { k : w.Checkbox(description=k,value=False,disabled=True) for k in self.simple_cmds.keys() }
#		self.mdprog = { k : w.FloatProgress(value=0., min=0., max=1., description=k, orientation='horizontal') for k in self.mdruns.keys() }

		self.children = [
			w.HTML('''Perform preparation of the molecule for MD in a batch -- 
apply force field, solvate, add counterions, minimize, 
run short isothermal-isochoric and isothermal-isobaric constrained simulations'''),
			w.Label("TODO: params"),
			self.startbutton,
			w.HTML('<h4>Progress</h4>'),
			self.progress
#			w.HBox([
#				w.VBox([w.Label('Initial steps')] + list(self.initprep.values()),layout=w.Layout(**main.ldict)),
#				w.VBox([w.Label('Short simulations')] + list(self.mdprog.values()),layout=w.Layout(**main.ldict))],
#				layout=w.Layout(**main.ldict)
#			)
			
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


	def _button_reset(self):
		self.startbutton.description = 'Start'
		self.startbutton.button_style = ''

	def status(self):
		cwd = self.main.select.cwd()
		self.startbutton.description = '... running ...'
		self.startbutton.button_style = 'info'

		simple = 'pdb2gmx gro2pdb editconf solvate genion'.split()
		mdruns = dict(minimize=('em.log',1000), nvt=('nvt.log',50000), npt=('npt.log',50000))

		if not self.gmx:
			self.gmx = GMX(workdir=cwd,pvc=self.main.pvc)
			with open(f'{cwd}/warmup.sh','w') as f:
				f.write(f'''#!/bin/bash
echo pdb2gmx >phase &&
gmx pdb2gmx -f orig.pdb -o mol.gro -p mol.top -water tip3p -ff amber94 -ignh &&
echo gro2pdb >phase &&
gmx pdb2gmx -f mol.gro -o mol.pdb -p shit.top -water tip3p -ff amber94 &&
echo editconf >phase &&
gmx editconf -f mol.gro -o box.gro -c -d {self.mdbox.value} -bt dodecahedron &&
echo solvate >phase &&
gmx solvate -cp box.gro -cs spc216.gro -o solv.gro -p mol.top &&
echo genion >phase &&	
gmx grompp -f ../ions.mdp -c solv.gro -p mol.top -o ions.tpr &&
gmx genion -s ions.tpr -o ions.gro -p mol.top -pname NA -nname CL -neutral <<<"13" &&
rm -f em.log && echo minimize >phase &&
gmx grompp -f ../minim-sol.mdp -c ions.gro -p mol.top -o em.tpr &&
gmx mdrun -v -deffnm em -pin on &&
rm -f nvt.log && echo nvt >phase &&
gmx grompp -f ../nvt.mdp -c em.gro -r em.gro -p mol.top -o nvt.tpr &&
gmx mdrun -v -deffnm nvt -pin on &&
rm -f npt.log && echo npt >phase &&
gmx grompp -f ../npt.mdp -c nvt.gro -r nvt.gro -t nvt.cpt -p mol.top -o npt.tpr &&
gmx mdrun -v -deffnm npt -pin on
''')
			os.chmod(f'{cwd}/warmup.sh',0o700)
			self.gmx.start('./warmup.sh',gmx=False,gpus=self.main.gpus)

		while True:
			stat = self.gmx.cooked()
#			print("cooked -> ",stat)
			if not stat:
				self.main.msg.value = 'Cannot read gromacs status'
				self._button_reset()
				return 'error'

			if stat == 'running':
				phase = simple[0]
				try:
					with open(f'{cwd}/phase') as f:
						phase = f.readline().rstrip()
				except FileNotFoundError:
					pass

				if phase in simple:
					self.progress.value = simple.index(phase)
					yield 'running',phase,.1

				else:
					s=0.
					try: 
						with open(f"{cwd}/{mdruns[phase][0]}") as log:
							lines = log.readlines()
							for l in reversed(lines):
								if re.match('\s+Step\s+Time',l):
									s = float(re.match('\s+(\d+)\s+',prev).group(1))
									break
								prev = l
					except FileNotFoundError:
						pass

					self.progress.value = len(simple) + mdprscale * (list(mdruns.keys()).index(phase) + s / mdruns[phase][1])
					yield 'running',phase,2

			elif stat == 'done':
					self.progress.value = self.progress.max
					self.gmx.delete()
					self._button_reset()
					return 'idle'
					
			elif stat == 'error':
				log = self.gmx.log()
				self.main.msg.value = log if log else 'Unknown gromacs error'
				self._button_reset()
				return 'error'

			elif stat == 'starting': 
				yield 'starting','',.1


	def gather_status(self,stat):
		mystat = dict()

		if self.gmx and self.gmx.name:
			mystat['gmx'] = self.gmx.name

		mystat['progress'] = self.progress.value

#		for k in self.simple_cmds.keys():
#			mystat[k] = self.initprep[k].value

#		for k in self.mdruns.keys():
#			mystat[k] = self.mdprog[k].value

#		if self.phase is not None: mystat['phase'] = self.phase
#		if self.mdpp is not None: mystat['mdpp'] = self.mdpp
		stat['warmup'] = mystat

	def restore_status(self,stat):
		self._button_reset()
		mystat = stat['warmup']
		if 'gmx' in mystat:
			self.gmx = GMX(workdir=f'{self.main.select.cwd()}',pvc=self.main.pvc)
			self.gmx.name = mystat['gmx']
		self.progress.value = mystat['progress']
		
#		for k in self.simple_cmds.keys():
#			self.initprep[k].value = mystat[k]

#		for k in self.mdruns.keys():
#			self.mdprog[k].value = mystat[k] 
	
#		self.phase = mystat['phase'] if 'phase' in mystat else None
#		self.mdpp = mystat['mdpp'] if 'mdpp' in mystat else None

	def reset_status(self):
		self._button_reset()
		self.gmx = None
		self.progress.value = 0.
#		self.phase = None
#		self.mdpp = None
		
#		for k in self.simple_cmds.keys():
#			self.initprep[k].value = False

#		for k in self.mdruns.keys():
#			self.mdprog[k].value = 0.
