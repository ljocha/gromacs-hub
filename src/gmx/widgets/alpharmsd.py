import ipywidgets as w
import gmx.widgets as gw

class AlphaRMSD(w.VBox):
	def __init__(self,main):
		super().__init__()
		self.main = main
		self.residues = w.Text(description='Residues',value='!! specify !!')
		self.r0 = w.FloatText(description='R_0',value=0.08)
		self.d0 = w.FloatText(description='D_0',value=0.)
		self.nn = w.IntText(description='NN',value=8)
		self.mm = w.IntText(description='MM',value=12)
		self.generate = w.Button(description='Generate')
		self.generate.on_click(self._generate)
		self.dat = w.Textarea(layout = w.Layout(height='5ex',**main.ldict))

		self.children = [
			w.HTML('''
Alpha RMSD collective variable reflecting how well are alpha-helices formed,
 see <a href="https://www.plumed.org/doc-v2.8/user-doc/html/_a_l_p_h_a_r_m_s_d.html" class="cm-link">Plumed manual</a>.
<h4>Parameters</h4>
'''),
			self.residues, self.r0, self.d0, self.nn, self.mm,
			w.HTML('<h4>plumed.dat fragment</h4>'),
			self.generate,
			self.dat
		]


	def _generate(self,e):
		self.main.msg.value = ''
		self.dat.value = f"alpharmsd: ALPHARMSD RESIDUES={self.residues.value} R_0={self.r0.value} D_0={self.d0.value} NN={self.nn.value} MM={self.mm.value}\n"


	def gather_status(self,stat):
		stat['alpharmsd'] = dict(
			residues=self.residues.value,
			r0=self.r0.value,
			d0=self.d0.value,
			nn=self.nn.value,
			mm=self.mm.value,
			dat=self.dat.value
		)

	def restore_status(self,stat):
		if 'alpharmsd' not in stat:
			self.reset_status()
		else:
			ms = stat['alpharmsd']
			self.residues.value = ms['residues']
			self.r0.value = ms['r0']
			self.d0.value = ms['d0']
			self.nn.value = ms['nn']
			self.mm.value = ms['mm']
			self.dat.value = ms['dat']


	def reset_status(self):
		self.residues.value = '!! specify !!'
		self.r0.value = .08
		self.d0.value = 0.
		self.nn.value = 8
		self.mm.value = 12
		self.dat.value = ''

