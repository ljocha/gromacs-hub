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
				self.stat = self.who.started(self.what)

				if self.stat == 'running':
					self.showstat.value = 'Running'
					sleep = 5
				else:
					sleep = 2

			elif self.stat == 'running':
				self.stat,self.what = self.who.finished(self.what)
				sleep = 5 if self.stat == 'running' else 1

			elif self.stat == 'error':
				if self.showstat.value != 'Error':
					self.showstat.value = 'Error'
				sleep = 1
					

			self.lock.release()
			time.sleep(sleep)
			


	def start(self,what,who):
		self.lock.acquire()
		if self.stat == 'idle' or self.stat == 'error':
			self.stat = 'start'
			self.what = what
			self.who = who
			self.main.msg.value = ''
		
		self.lock.release()
