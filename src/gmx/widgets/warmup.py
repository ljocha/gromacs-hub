import ipywidgets as w
from gmx.wrapper import GMX
import os

class Warmup(w.VBox):
	def __init__(self,main,**kwargs):
		super().__init__(**kwargs)
		self.main = main

		self.startbutton = w.Button(description='Start')
		self.children = [ w.Label("TODO: params"), self.startbutton ]


		self.startbutton.on_click(lambda e: self.main.status.start('pdb2gmx',self))


	def start(self,what):
		mdbox = 2.0
		self.simple_cmds = {
			"pdb2gmx": "pdb2gmx -f orig.pdb -o mol.gro -p mol.top -water tip3p -ff amber94 -ignh",
			"editconf": f"editconf -f mol.gro -o box.gro -c -d {mdbox} -bt dodecahedron",
			"solvate": "solvate -cp box.gro -cs spc216.gro -o solv.gro -p mol.top",
			"grompp-ions": "grompp -f ../ions.mdp -c solv.gro -p mol.top -o ions.tpr",
			"genion": ("genion -s ions.tpr -o ions.gro -p mol.top -pname NA -nname CL -neutral","13"),
		}

		self.gmx = GMX(workdir=f'{self.main.select.cwd()}',pvc=self.main.pvc)

		if what in self.simple_cmds:
			if isinstance(self.simple_cmds[what],tuple):
				self.gmx.start(self.simple_cmds[what][0],input=self.simple_cmds[what][1])
			else:
				self.gmx.start(self.simple_cmds[what])

	def started(self,what):
		if what in self.simple_cmds:
			stat = self.gmx.status()
			
			if not stat.failed:
				return 'running' if stat.active else 'starting'
			else:
				log = self.gmx.log()
				self.main.msg.value = log
				return 'error'

	def finished(self,what):
		stat = self.gmx.status()
		if stat.succeeded:
			cmds = self.simple_cmds.keys()
			for i,c in enumerate(cmds):
				if c == what: break

			if i < len(cmds)-1:
				return 'start',list(cmds)[i+1]
			else:
				return 'idle',None

		else:
			if stat.failed:
				log = self.gmx.log()
				self.main.msg.value = log
				return 'error',what
			else:
				return 'running',what
