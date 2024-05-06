#!/bin/bash

export nnodes=1
export nodetype=cpu
export walltime=00:20:00
export nodename=vk-nersc-test
export site=perlmutter
export kubelet_port=10000
export account=m4637

docker run -it --rm --name=lpad \
 -e nnodes=$nnodes -e nodetype=$nodetype \
  -e walltime=$walltime -e nodename=$nodename -e site=$site -e kubelet_port=$kubelet_port -e account=$account jlabtsai/jrm-fw:latest bash # lpad -l /fw/my_launchpad.yaml reset 


