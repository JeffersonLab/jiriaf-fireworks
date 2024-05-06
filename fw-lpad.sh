#!/bin/bash


docker run -it --rm --name=lpad -v `pwd`/FireWorks:/fw  jlabtsai/fw-lpad /bin/bash -c "lpad -l /fw/my_launchpad.yaml get_wflows -t"

shifter --image=docker:jlabtsai/fw-lpad /bin/bash -c "lpad -l my_launchpad.yaml get_wflows -t"