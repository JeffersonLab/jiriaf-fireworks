#!/bin/bash

export nnodes=1
export nodetype=cpu
export walltime=00:20:00 # this is the walltime for the slurm job and jrm walltime
export nodename=vk-nersc-test
export site=perlmutter
export kubelet_port=10000 # this should be unique for each jrm including those with the status notready. Delete the notready jrm if you want to reuse the port.
export account=m4637 # this is the account number for the allocation at NERSC

mkdir -p $HOME/jrm-launch/logs
export logs="$HOME/jrm-launch/logs"

docker run -it --rm --name=jrm-fw -v $logs:/fw/logs \
 -e nnodes=$nnodes -e nodetype=$nodetype \
  -e walltime=$walltime -e nodename=$nodename -e site=$site -e kubelet_port=$kubelet_port -e account=$account jlabtsai/jrm-fw:latest $1 # lpad -l /fw/my_launchpad.yaml reset 


