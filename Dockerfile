FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y --no-install-recommends python3-venv && apt clean && rm -rf /var/lib/apt/lists/*

COPY start-hub.sh /usr/local/bin
RUN mkdir /opt/gmx && chown 1000 /opt/gmx
RUN mkdir /home/jovyan && chown 1000 /home/jovyan

USER 1000

RUN python3 -m venv /opt/gmx


RUN . /opt/gmx/bin/activate && pip3 install voila notebook 
RUN . /opt/gmx/bin/activate && pip3 install ipywidgets 
# RUN . /opt/gmx/bin/activate && pip3 install jupyterhub 


COPY gmx-main.ipynb /home/jovyan

ENV HOME /home/jovyan
