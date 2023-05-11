image=ljocha/gromacs-hub
tag=2023-17rf1
ns=gmxhub-ns
devns=krenek-ns
port=8055

flags=--rm -ti -v ${PWD}:/work -w /work  -p ${port}:${port} -u ${shell id -u} -e HOME=/work

#package_name=gmx-0.0.1.tar.gz
package_name=gmx-0.0.1-py3-none-any.whl
package=dist/${package_name}

build: ${package}
	docker build -t ${image}:${tag} .
	docker push ${image}:${tag}

${package} build-gmx:
	python3 -m build

bash:
	docker run ${flags} ${image}:${tag} bash

ntb:
	docker run ${flags} ${image}:${tag} bash -c ". /opt/gmx/bin/activate; jupyter notebook --ip 0.0.0.0 --port ${port} --VoilaConfiguration.file_whitelist='.*'"

voila:
	docker run ${flags} ${image}:${tag} bash -c ". /opt/gmx/bin/activate; voila /opt/gmx/lib/gmx-main.ipynb --Voila.ip 0.0.0.0 --port ${port} --VoilaConfiguration.file_whitelist=\"['.*']\""


install:
	helm install gromacs-hub -n ${ns} jupyterhub/jupyterhub -f helm/values.yaml \
		--set hub.config.GenericOAuthenticator.client_secret=${shell cat helm/client_secret} \
 		--set hub.config.notebookImage=${image}:${tag} \
		--set-file hub.extraConfig.form-0=helm/form-0.py\
		--set-file hub.extraConfig.form-1=helm/form-1.py\
		--set-file hub.extraConfig.pre-spawn-hook=helm/pre-spawn-hook.py

uninstall:
	helm uninstall gromacs-hub -n ${ns}

devpod=${shell kubectl -n ${devns} get pods | grep gromacs-portal-dev | awk '{print $$1}'}

devinstall:
	kubectl -n ${devns} apply -f k8s-dev/service.yaml
	kubectl -n ${devns} apply -f k8s-dev/ingress.yaml
	sed s?IMAGE?${image}:${tag}? k8s-dev/deployment.yaml | kubectl -n ${devns} apply -f -

devuninstall:
	kubectl -n ${devns} delete service/gromacs-portal-dev ingress.networking.k8s.io/gromacs-portal-dev deployment.apps/gromacs-portal-dev 

devbash:
	kubectl -n ${devns} exec -ti pod/${devpod} -- bash

devtoken:
	kubectl -n ${devns} logs pod/${devpod} | grep token=

devntb:
	kubectl cp ${devns}/${devpod}:/home/jovyan/gmx-main.ipynb gmx-main.ipynb

devdeploy: ${package}
	kubectl cp ${package} ${devns}/${devpod}:/var/tmp/${package_name}
	kubectl exec -n ${devns} ${devpod} -- bash -c ". /opt/gmx/bin/activate && pip uninstall -y gmx && pip install /var/tmp/${package_name}"

devputgmx:
	kubectl cp src/gmx/gmx.py ${devns}/${shell kubectl -n ${devns} get pods | grep gromacs-portal-dev | awk '{print $$1}'}:/opt/gmx/lib/python3.10/site-packages/gmx/gmx.py

repo:
	helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
	helm repo update
