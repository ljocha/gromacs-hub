FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y --no-install-recommends python3-venv && apt clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /opt/gmx && chown 1000 /opt/gmx

USER 1000

RUN python3 -m venv /opt/gmx


RUN . /opt/gmx/bin/activate && pip3 install voila notebook 
RUN . /opt/gmx/bin/activate && pip3 install ipywidgets 
