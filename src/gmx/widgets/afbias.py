import ipywidgets as w
import urllib.request
import zipfile as z
import json
import pickle
import numpy as np
import mdtraj as md

class AFBias(w.VBox):
	def __init__(self,main):
		super().__init__(layout=w.Layout(**main.ldict))
		self.main = main
		self.url = w.Text(description='URL')
		self.download = w.Button(description='Download')
		self.download.on_click(self._download)

		self.models = w.Dropdown(description='Models')
		self.generate = w.Button(description='Generate')
		self.generate.on_click(self._generate)

		self.epsilon = w.FloatText(value=0.00001,description='Epsilon')

		self.dat = w.Textarea(description='plumed.dat',layout = w.Layout(height='50ex',**main.ldict))

		self.children = [
			w.HTML('''
<p>
Prepare fragment of <a href="http://plumed.org/" class="cm-link">Plumed</a> input file
based on AlphaFold intermediate outputs. 
The collective variable can be interpreted as a probabilistically based measure to assess how 
AlphaFold would favor the current conformation.
See <a href="https://doi.org/10.3389/fmolb.2022.878133" class="cm-link">Spiwok et al, 2022</a>
for details. 
</p>
<p>
Provide a download link for a zipfile of a folder with AlphaFold results.
It was tested with our <a href="http://alphafold.cloud.e-infra.cz/" class="cm-link">twin service</a>, 
run the calculation there (for temporary technical reasons only the basic <i>AlphaFold</i> method
is compatible with this portal,
not <i>CollabFold</i> or others), generate download link, and paste it here.
</p>
'''),
			w.HBox([self.url, self.download],layout=w.Layout(**main.ldict)),
			w.HTML('''
<p>
After parsing the file, the dropdown menu bellow is populated with available models 
sorted according to their confidence.
<i>Epsilon</i> is stabilizing term in softmax interpolation (see the paper),
increase it if the subsequent MD crashes becaouse of too high energy, high velocity etc.
</p>
'''),
			w.HBox([self.models, self.epsilon, self.generate],layout=w.Layout(**main.ldict)),
			self.dat
		]

	def _download(self,e):
		cwd = self.main.select.cwd()
		try:
			self.main.msg.value = ''
			self.download.disabled = True
			self.download.description = 'downloading...'
			urllib.request.urlretrieve(self.url.value,f'{cwd}/af.zip')
			self.download.description = 'parsing...'
			self._parse_zip()
		except Exception as e:
			self.main.msg.value = str(e)
		finally:
			self.download.disabled = False
			self.download.description = 'Download'

		self.main.status.savestat(lock=True)

	def _parse_zip(self):
		cwd = self.main.select.cwd()
		with z.ZipFile(f'{cwd}/af.zip') as zf:
			files = zf.namelist()
			m = None
			for m in files:
				if 'ranking_debug.json' in m:
					break

			if not m:
				raise ValueError('ranking_debug.json not found')
		
			with zf.open(m) as mf:
				models = json.load(mf)

			self.models.options = [
				f'{m[0]}: {m[1]}'
				for m in sorted(models['plddts'].items(), key=lambda x: -x[1])
			]
			self.models.value = self.models.options[0]
			
	def _generate(self,e):
		self.main.msg.value = ''
		try:
			cwd = self.main.select.cwd()
			mn = self.models.value.split(':')[0]
			with z.ZipFile(f'{cwd}/af.zip') as zf:
				for fn in zf.namelist():
					if mn in fn: break
				with zf.open(fn) as pf:
					data = pickle.load(pf)

			gro = md.load(f'{cwd}/npt.gro')
			atoms = gro.topology.select('name CA') + 1
			ncas = atoms.shape[0]
			natoms = gro.topology.select('protein').shape[0]
				
			bins = data['distogram']['bin_edges']
			bins = np.append(bins,2*bins[-1]-bins[-2])
			logits = data['distogram']['logits']
			logits = np.where(logits > 50, 50, logits)
			probs = np.exp(logits)/(1.0 + np.exp(logits))
			sumprobs = probs.sum(axis=2)
			probs2 = probs
			for i in range(len(atoms)):
			  for j in range(len(atoms)):
			    probs2[i,j,:] = probs[i,j,:]/sumprobs[i,j]
		
			plmd = [
#				f"WHOLEMOLECULES ENTITY0=1-{natoms}",
				"AF_DISTPROB ...",
				"LABEL=afscore",
			  f"ATOMS={','.join(map(str,atoms))}",
				"LAMBDA=1000",
				f"EPSILON={self.epsilon.value}",
				f"DISTANCES={','.join(map(str,bins/10.))}"
			] + [
				f"PROB_MATRIX{k}={','.join([ str(probs2[i,j,k]) for i in range(ncas) for j in range(ncas) ])}"
				for k in range(64)
			] + [
				"... AF_DISTPROB",
#				"PRINT ARG=afscore STRIDE=100 FILE=COLVAR"
			]

			self.dat.value = '\n'.join(plmd) + '\n'
#			with open(f'{cwd}/af-plumed.dat','w') as p:
#				p.write(self.dat.value)
		
		except Exception as e:
			self.main.msg.value = str(e)


	def gather_status(self,stat):
		mystat = dict()
		mystat['url'] = self.url.value
		mystat['model'] = self.models.value
		mystat['dat'] = self.dat.value
		stat['afbias'] = mystat

	def restore_status(self,stat):
		try:
			mystat = stat['afbias']
			self.url.value = mystat['url']
			if self.url.value:
				self._parse_zip()
	
			self.models.value = mystat['model']
			self.dat.value = mystat['dat']
		except KeyError:
			self.reset_status()
			
	def reset_status(self):
		self.url.value = ''
		self.models.value = None
		self.models.options = []
