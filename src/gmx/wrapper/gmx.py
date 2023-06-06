import kubernetes as k8s
import tempfile
import yaml
import uuid
import os
import time

class GMX:
	def __init__(self,pvc=None,image='ljocha/gromacs:2023-1',workdir='ASMSA'):
		self.pvc = pvc
		self.name = None
		self.workdir = workdir
		self.ns = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()
		self.image = image
		k8s.config.load_incluster_config()
		self.batchapi = k8s.client.BatchV1Api()
		self.coreapi = k8s.client.CoreV1Api()

	def start(self,cmd=None,input=None,gpus=0,gputype='mig-1g.10gb',cores=1,mem=4,wait=False,delete=False,tail=10):
		
		if self.name:
			raise RuntimeError(f"job {self.name} already running, delete() it first")

		if isinstance(cores,int):
			cores = (cores,cores)
			
		self.name = "gmx-" + str(uuid.uuid4())

		if cmd is None:
			kcmd = [ 'sleep', '365d' ]

		else:
			if isinstance(cmd,list):
				cmd = ' '.join(map(lambda s: f'"{s}"',cmd))
	
			if input is not None:
				cmd += f' <<<"{input}"'
			
			kcmd = ['bash', '-c', 'gmx ' + cmd]
			
		yml = f"""\
apiVersion: batch/v1
kind: Job
metadata:
  name: {self.name}
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: {self.name}
        image: {self.image}
        workingDir: /mnt/{self.workdir}
        command: {kcmd}
        securityContext:
          runAsUser: 1000
          runAsGroup: 1000
        env:
        - name: 'OMP_NUM_THREADS'
          value: '{cores[0]}'
        resources:
          requests:
            cpu: '{cores[1]}'
            memory: {mem}Gi
            nvidia.com/{gputype}: {gpus}
          limits:
            cpu: '{cores[0]}'
            memory: {mem}Gi
            nvidia.com/{gputype}: {gpus}
        volumeMounts:
        - name: vol-1
          mountPath: /mnt
      volumes:
      - name: vol-1
        persistentVolumeClaim:
          claimName: {self.pvc}
"""
				
		yml = yaml.safe_load(yml)
		self.job = self.batchapi.create_namespaced_job(self.ns,yml)

		if wait:
#			print(self.status().succeeded)
			while not self.status().succeeded:
#				print(self.status().succeeded)
				print('.',end='')
				time.sleep(2)
			print()

			self.log(tail=tail)
			if delete:
				self.delete()

	def exec(self,cmd,input=None):
		if isinstance(cmd,list):
			cmd = ' '.join(map(lambda s: f'"{s}"',cmd))

		if input is not None:
			cmd += f' <<<"{input}"'
		
		kcmd = ['bash', '-c', 'gmx ' + cmd]
			
		if self.name:
			while not self.status().ready:
				time.sleep(1)

			pod = self.coreapi.list_namespaced_pod(self.ns,label_selector=f'job-name={self.name}').items[0].metadata.name

			resp = k8s.stream.stream(self.coreapi.connect_get_namespaced_pod_exec,
													pod, self.ns,
													command=kcmd,
													stderr=True, stdin=False, stdout=True, tty=False)

			return resp
		return None

	def status(self,pretty=True):
		if self.name:
			try:
				return self.batchapi.read_namespaced_job(self.name, self.ns, pretty=pretty).status
			except k8s.client.exceptions.ApiException:
				return None
		return None

	def cooked(self):
		stat = self.status()
		if stat:
			if stat.failed: return 'error'
			if stat.succeeded: return 'done'
			if stat.active and not stat.ready: return 'starting'
			if stat.active: return 'running'
			if not stat.active: return 'starting'
			print(stat)
			raise ValueError('unknown status')
		return None
		
	def delete(self):
		if self.name:
			try:
				l = self.coreapi.list_namespaced_pod(self.ns,label_selector=f'job-name={self.name}')
				for i in l.items:
					self.coreapi.delete_namespaced_pod(i.metadata.name, self.ns)
				self.batchapi.delete_namespaced_job(self.name, self.ns)
			except k8s.client.exceptions.ApiException:
				pass
			self.name = None
		return None

	def kill(self):
		if self.name:
			os.system(f"kubectl -n {self.ns} exec job/{self.name} -- kill 1")
		
	def log(self, tail=None):
		out = None
		if self.name:
			with os.popen(f"kubectl logs job/{self.name}") as p:
				if tail:
					out = ''.join(p.readlines()[:-tail])
				else:
					out = ''.join(p.readlines())

		return out
