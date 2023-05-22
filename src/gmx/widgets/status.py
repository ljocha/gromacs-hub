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

	def _watch(self):
		self.watching = True
		while (not self.stop):
			sleep = 1
			self.lock.acquire()
			
			if self.stat == 'idle' or self.stat == 'error':
				ucfirst = self.stat[0].upper() + self.stat[1:]
				if self.showstat.value != ucfirst:
					self.showstat.value = ucfirst
					if self.stat == 'idle':
						self.showphase.value = ''

			elif self.stat == 'start':
				self.stat = 'starting'
				self.showstat.value = 'Starting'
				self.showphase.value = ''
				self.watch = self.who.status()

			else:
				try:
					self.stat,self.showphase.value,sleep = next(self.watch)
					self.showstat.value = self.stat[0].upper() + self.stat[1:]
				except StopIteration as e:
					self.stat = e.args[0]

			self.savestat()
			self.lock.release()
			time.sleep(sleep)
			
		self.watching = False

	def savestat(self,lock=False):
		if lock: self.lock.acquire()
		savestat = dict()
		self.main.gather_status(savestat)
		cwd = self.main.select.cwd()
		if cwd:
			with open(f'{cwd}/status.json.new','w') as j:
				json.dump(savestat,j,indent=2)

			os.rename(f'{cwd}/status.json.new',f'{cwd}/status.json')

		if lock: self.lock.release()



	def start_watch(self):
		self.stop = False
		_thread.start_new_thread(self._watch,())

	def stop_watch(self):
		self.stop = True
		while self.watching:
			time.sleep(1)


	def start(self,who):
		self.lock.acquire()
		if self.stat == 'idle' or self.stat == 'error':
			self.stat = 'start'
			self.who = who
			self.main.msg.value = ''
		
		self.lock.release()


	def gather_status(self,stat):
		mystat = dict()
		mystat['stat'] = self.stat
		mystat['who'] = type(self.who).__name__
		stat['status'] = mystat

	def restore_status(self,stat):
		self.lock.acquire()
		try:
			mystat = stat['status']
			self.stat = mystat['stat']
			self.showstat.value = self.stat[0].upper() + self.stat[1:]
			if mystat['who'] == 'Warmup':
				self.who = self.main.ctrl.warmup
			elif mystat['who'] == 'MD':
				self.who = self.main.ctrl.md
			else:
				self.who = None
	
			if self.who and self.stat != 'idle' and self.stat != 'error':
				self.watch = self.who.status()

		finally:
			self.lock.release()

	def reset_status(self):
		self.lock.acquire()
		self.stat = 'idle'
		self.showstat.value = self.stat[0].upper() + self.stat[1:]
		self.showphase.value = ''
		self.who = None
		self.lock.release()
