import ipywidgets as w

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
			"grompp-ions": "grompp -f ions.mdp -c solv.gro -p ions.top -o ions.tpr",
			"genion": ("genion -s ions.tpr -o ions.gro -p ions.top -pname NA -nname CL -neutral","13"),
		}

		if what in self.simple_cmds:
			if isinstance(self.simple_cmds[what],tuple):
				self.main.gmx.start(self.simple_cmds[what][0],input=self.simple_cmds[what][1])
			else:
				self.main.gmx.start(self.simple_cmds[what])

	def started(self,what):
		if what in self.simple_cmds:
			if not self.main.gmx.status().failed:
				print(self.main.gmx.status())
				return 'running'

	def finished(self,what):
		print(self.main.gmx.status())
		if self.main.gmx.status().succeeded:
			cmds = self.simple_cmds.keys()
			for i,c in enumerate(cmds):
				if c == what: break

			if i < len(cmds)-1:
				return 'start',cmds[i+1]
			else:
				return 'idle',None

		else:
			return 'running',what
