FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y --no-install-recommends python3-dev python3-venv g++ && apt clean && rm -rf /var/lib/apt/lists/*

COPY start-hub.sh /usr/local/bin
RUN mkdir /opt/gmx && chown 1000 /opt/gmx
RUN mkdir /home/jovyan && chown 1000 /home/jovyan

USER 1000

RUN python3 -m venv /opt/gmx


RUN . /opt/gmx/bin/activate && pip3 install notebook 
RUN . /opt/gmx/bin/activate && pip3 install 'ipywidgets<8'
# RUN . /opt/gmx/bin/activate && pip3 install jupyterhub 
RUN . /opt/gmx/bin/activate && pip3 install nglview mdtraj 

RUN . /opt/gmx/bin/activate && pip3 install 'voila<0.4.0'
RUN . /opt/gmx/bin/activate && jupyter serverextension enable voila --sys-prefix

COPY gmx-main.ipynb /opt/gmx/lib

WORKDIR /home/jovyan
ENV HOME /home/jovyan

USER 0
RUN apt update && apt install -y vim curl && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && install -m 755 kubectl /usr/local/bin && apt clean && rm -rf /var/lib/apt/lists/*

USER 1000

COPY dist/gmx-0.0.1.tar.gz /tmp
RUN . /opt/gmx/bin/activate && pip3 install /tmp/gmx-0.0.1.tar.gz
