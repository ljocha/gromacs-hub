import ipywidgets as w
from gmx.wrapper import GMX
import os
import re

class Warmup(w.VBox):
	def __init__(self,main,**kwargs):
		super().__init__(**kwargs)
		self.main = main
		self.gmx = None
		self.mdpp = False

		self.startbutton = w.Button(description='Start')

		mdbox = 2.0
		self.simple_cmds = {
			"pdb2gmx": "pdb2gmx -f orig.pdb -o mol.gro -p mol.top -water tip3p -ff amber94 -ignh",
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
			w.Label("TODO: params"),
			self.startbutton,
			w.Label('Progress'),
			w.HBox(list(self.initprep.values())),
			w.HBox(list(self.mdprog.values())),
		]


		self.startbutton.on_click(lambda e: self.main.status.start('pdb2gmx',self))

	def start(self,what):
		if what == 'pdb2gmx':
			self.gmx = GMX(workdir=f'{self.main.select.cwd()}',pvc=self.main.pvc)
			for c in self.initprep.values():
				c.value = False
			for p in self.mdprog.values():
				p.value = 0.
			self.mdpp = True

		if what in self.simple_cmds:
			if isinstance(self.simple_cmds[what],tuple):
				self.gmx.start(self.simple_cmds[what][0],input=self.simple_cmds[what][1])
			else:
				self.gmx.start(self.simple_cmds[what])

		if what in self.mdruns:
			if self.mdpp:
				self.gmx.start(self.mdruns[what][0])
			else:
				try:
					os.remove(f"{self.main.select.cwd()}/{self.mdruns[what][2]}")
				except FileNotFoundError:
					pass

				self.gmx.start(self.mdruns[what][1],gpus=self.main.gpus)

	def started(self,what):
#		if what in self.simple_cmds:
			stat = self.gmx.status()
			
			if not stat.failed:
				return 'running' if stat.active else 'starting'
			else:
				log = self.gmx.log()
				self.main.msg.value = log
				self.gmx.delete()
				return 'error'

	def finished(self,what):
		stat = self.gmx.status()
		if stat.succeeded:
			self.gmx.delete()
			if what in self.simple_cmds:
				self.initprep[what].value = True
				cmds = self.simple_cmds.keys()
				for i,c in enumerate(cmds):
					if c == what: break
	
				if i < len(cmds)-1:
					return 'start',list(cmds)[i+1]
				else:
					return 'start','minimize'

			if what in self.mdruns:
				cmds = self.mdruns.keys()
				for i,c in enumerate(cmds):
					if c == what: break
	
				if self.mdpp:
					self.mdpp = False
					return 'start',what
				else:
					self.mdprog[what].value = 1.
					self.mdpp = True
					if i < len(cmds)-1:
						return 'start',list(cmds)[i+1]
					else:
						return 'idle',None
		
		else:
			if stat.failed:
				log = self.gmx.log()
				self.main.msg.value = log
				self.gmx.delete()
				return 'error',what
			else:
				if not self.mdpp:
					s = 0.
					try:
						with open(f"{self.main.select.cwd()}/{self.mdruns[what][2]}") as log:
							lines = log.readlines()
							for l in reversed(lines):
								if re.match('\s+Step\s+Time',l):
									s = float(re.match('\s+(\d+)\s+',prev).group(1))
									break
								prev = l
					except FileNotFoundError:
						pass
	
					self.mdprog[what].value = s / self.mdruns[what][3]
		

				return 'running',what


	def gather_status(self,stat):
		mystat = dict()

		if self.gmx and self.gmx.name:
			mystat['gmx'] = self.gmx.name

		for k in self.simple_cmds.keys():
			mystat[k] = self.initprep[k].value

		for k in self.mdruns.keys():
			mystat[k] = self.mdprog[k].value

		mystat['mdpp'] = self.mdpp

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
#			print(f'{k}: {mystat[k]}')
	
		self.mdpp = mystat['mdpp']

	def reset_status(self):
		self.gmx = None
		
		for k in self.simple_cmds.keys():
			self.initprep[k].value = False

		for k in self.mdruns.keys():
			self.mdprog[k].value = 0.
	
		self.mdpp = False
