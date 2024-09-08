#!/bin/bash

#set -x

export logs="$HOME/jrm-launch/logs"

docker_tag="api-in-container"

docker pull jlabtsai/jrm-fw:$docker_tag

docker run -it --rm --net=host -v $logs:/fw/logs -v ./perl-config.yaml:/fw/per-config.yaml -v ./ornl-config.yaml:/fw/ornl-config.yaml -v `pwd`/port_table.yaml:/fw/port_table.yaml -v $HOME/.ssh/nersc:/root/.ssh/nersc jlabtsai/jrm-fw:$docker_tag