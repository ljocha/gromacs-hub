image=ljocha/gromacs-hub
tag=2023-3
port=8055

flags=-ti -v ${PWD}:/work -w /work  -p ${port}:${port} -u ${shell id -u} -e HOME=/work

build:
	docker build -t ${image}:${tag} .
	docker push ${image}

bash:
	docker run ${flags} ${image}:${tag} bash

ntb:
	docker run ${flags} ${image}:${tag} bash -c ". /opt/gmx/bin/activate; jupyter notebook --ip 0.0.0.0 --port ${port}"


install:
	helm install gromacs-hub -n krenek-ns jupyterhub/jupyterhub -f helm/values.yaml \
		--set hub.config.GenericOAuthenticator.client_secret=${shell cat helm/client_secret} \
 		--set hub.config.notebookImage=${image}:${tag} \
		--set-file hub.extraConfig.form-0=helm/form-0.py\
		--set-file hub.extraConfig.form-1=helm/form-1.py\
		--set-file hub.extraConfig.pre-spawn-hook=helm/pre-spawn-hook.py

uninstall:
	helm uninstall gromacs-hub -n krenek-ns

repo:
	helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
	helm repo update
