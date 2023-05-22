FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y --no-install-recommends python3-dev python3-venv g++ && apt clean && rm -rf /var/lib/apt/lists/*
RUN apt update && apt install -y vim curl less && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && install -m 755 kubectl /usr/local/bin && apt clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /opt/gmx && chown 1000 /opt/gmx
RUN mkdir /home/jovyan && chown 1000 /home/jovyan

USER 1000

RUN python3 -m venv /opt/gmx

RUN . /opt/gmx/bin/activate && pip3 install notebook  && rm -rf /home/jovyan/.cache
RUN . /opt/gmx/bin/activate && pip3 install 'ipywidgets<8' && rm -rf /home/jovyan/.cache
# RUN . /opt/gmx/bin/activate && pip3 install jupyterhub  && rm -rf /home/jovyan/.cache
RUN . /opt/gmx/bin/activate && pip3 install nglview mdtraj  && rm -rf /home/jovyan/.cache

RUN . /opt/gmx/bin/activate && pip3 install 'voila<0.4.0' && rm -rf /home/jovyan/.cache
RUN . /opt/gmx/bin/activate && jupyter serverextension enable voila --sys-prefix
RUN . /opt/gmx/bin/activate && pip3 install ipympl && jupyter nbextension install --py --sys-prefix --overwrite ipympl && jupyter nbextension enable --py --sys-prefix ipympl && rm -rf /home/jovyan/.cache

RUN . /opt/gmx/bin/activate && pip3 install 'jax<0.4' 'jaxlib<0.4' && rm -rf /home/jovyan/.cache

RUN mkdir /opt/gmx/home

WORKDIR /home/jovyan
ENV HOME /home/jovyan

USER 0
COPY start-hub.sh start-devel.sh /usr/local/bin/

USER 1000


COPY dist/gmx-0.0.1.tar.gz /tmp
RUN . /opt/gmx/bin/activate && pip3 install /tmp/gmx-0.0.1.tar.gz && rm -rf /home/jovyan/.cache

COPY gmx-main.ipynb ions.mdp minim-sol.mdp nvt.mdp npt.mdp md.mdp.template /opt/gmx/home/
