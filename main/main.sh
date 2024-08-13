#!/bin/bash

set -x

# Check if site argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <site>"
  exit 1
fi

export site=$1 # nersc / ornl
export env_list="/home/tsai/jrm-launch/main/env.list.$site"
export jrm_fw_tag=$site
export logs="$HOME/jrm-launch/logs"

docker pull jlabtsai/jrm-fw:$jrm_fw_tag

docker run -it --rm --name=jrm-fw -v $logs:/fw/logs --env-file $env_list jlabtsai/jrm-fw:$jrm_fw_tag "${@:2}"