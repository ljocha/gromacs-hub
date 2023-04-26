image=ljocha/gromacs-hub:2023-2
port=8055

flags=-ti -v ${PWD}:/work -w /work  -p ${port}:${port} -u ${shell id -u} -e HOME=/work

build:
	docker build -t ${image} .
	docker push ${image}

bash:
	docker run ${flags} ${image} bash

ntb:
	docker run ${flags} ${image} bash -c ". /opt/gmx/bin/activate; jupyter notebook --ip 0.0.0.0 --port ${port}"

install:
	helm install gromacs-hub -n krenek-ns jupyterhub/jupyterhub -f helm/values.yaml --set hub.config.GenericOAuthenticator.client_secret=${shell cat helm/client_secret}

uninstall:
	helm uninstall gromacs-hub -n krenek-ns
