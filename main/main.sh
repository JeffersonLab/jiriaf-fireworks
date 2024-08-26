#!/bin/bash

#set -x

export logs="$HOME/jrm-launch/logs"
export port_table=`pwd`/port_table.yaml

docker pull jlabtsai/jrm-fw:main

docker run -it --rm --name=jrm-fw -v $logs:/fw/logs -v $1:/fw/site_config.yaml -v $port_table:/fw/port_table.yaml  jlabtsai/jrm-fw:main "${@:2}"