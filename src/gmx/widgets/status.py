import ipywidgets as w
import threading
import time
import os
from gmx.wrapper import GMX

class Status(w.HBox):
	def __init__(self,main):
		super().__init__(layout = w.Layout(width='100%',display="flex", justify_content="flex-end"))

		self.main = main
		self.showstat = w.Label('Idle')
		self.showphase = w.Label()

		self.children = [self.showphase, self.showstat ]

		self.lock = threading.Lock()
		self.stat = 'idle'
		self.what = None
		self.who = None
		self.jobid = None
		self.gmx = GMX(workdir=f'{os.getcwd()}/{self.main.select.cwd()}')

		# TODO: recover status when revisiting the page


	def watch(self):
		while (True):
			self.lock.acquire()
			if self.stat == 'idle':
				if self.showstat.value != 'Idle':
					self.showstat.value = 'Idle'
					self.showphase.value = ''
				sleep = 1

			elif self.stat == 'start':
				self.stat = 'starting'
				self.showstat.value = 'Starting'
				self.showphase.value = self.what # XXX
				self.who.start(self.what)
				sleep = 1

			elif self.stat == 'starting':
				if self.who.started():
					self.stat = 'running'
					self.showstat.value = 'Running'
					sleep = 10
				else:
					sleep = 2

			elif self.stat == 'running':
				self.stat,self.what = self.who.finished()
				sleep = 10 if self.stat == 'running' else 1

			self.lock.release()
			time.sleep(sleep)
			


	def start(self,what,who):
		self.lock.acquire()
		if self.stat != 'start':
			self.stat = 'start'
			self.what = what
			self.who = who
		
		self.lock.release()
