import ipywidgets as w
import threading
import time
import os
import json
from gmx.wrapper import GMX

import _thread

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
		self.watching = False
		self.stop = False

		# TODO: recover status when revisiting the page


	def _watch(self):
		self.watching = True
		while (not self.stop):
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
					
			savestat = dict()
			self.main.gather_status(savestat)
			cwd = self.main.select.cwd()
			if cwd:
				with open(f'{cwd}/status.json.new','w') as j:
					json.dump(savestat,j,indent=2)

				os.rename(f'{cwd}/status.json.new',f'{cwd}/status.json')

			self.lock.release()
			time.sleep(sleep)
			
		self.watching = False

	def start_watch(self):
		self.stop = False
		_thread.start_new_thread(self._watch,())

	def stop_watch(self):
		self.stop = True
		while self.watching:
			time.sleep(1)


	def start(self,what,who):
		self.lock.acquire()
		if self.stat == 'idle' or self.stat == 'error':
			self.stat = 'start'
			self.what = what
			self.who = who
			self.main.msg.value = ''
		
		self.lock.release()


	def gather_status(self,stat):
		mystat = dict()
		mystat['stat'] = self.stat
		mystat['who'] = type(self.who).__name__
		mystat['what'] = self.what
		stat['status'] = mystat

	def restore_status(self,stat):
		self.lock.acquire()
		mystat = stat['status']
		self.stat = mystat['stat']
		self.showstat.value = self.stat[0].upper() + self.stat[1:]
		if mystat['who'] == 'Warmup':
			self.who = self.main.ctrl.warmup
		elif mystat['who'] == 'MD':
			self.who = self.main.ctrl.md

		self.what = mystat['what']
		self.lock.release()
