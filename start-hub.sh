#!/bin/bash

. /opt/gmx/bin/activate
cp /opt/gmx/home/* /home/jovyan
#jupyter notebook "$@"
#voila /opt/gmx/lib/gmx-main.ipynb --Voila.ip=0.0.0.0 --port 8888 "$@"
"$@"
