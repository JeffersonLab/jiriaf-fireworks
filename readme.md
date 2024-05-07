# README.md

## Overview

The `main.sh` script is a bash script used to set up and run a Docker container for launching Slurm jobs for deploying JRMs. The script sets several environment variables and then runs a Docker container with specific settings.

## Environment Variables

The script sets the following environment variables:

- `nnodes`: The number of nodes.
- `nodetype`: The type of node.
- `walltime`: The walltime for the slurm job and JRM.
- `nodename`: The name of the node.
- `site`: The site name.
- `kubelet_port`: The port for the kubelet. This should be unique for each JRM, including those with the status 'notready'. Delete the 'notready' JRM if you want to reuse the port.
- `account`: The account number for the allocation at NERSC.

## Log Directory

The script creates a directory at `$HOME/jrm-launch/logs` for storing logs. The path to this directory is stored in the `logs` environment variable.

## Docker Run

The script runs a Docker container with the following settings:

- Mount the log directory to `/fw/logs` in the container (`-v $log:/fw/logs`)
- Set the environment variables inside the container (`-e nnodes=$nnodes -e nodetype=$nodetype -e walltime=$walltime -e nodename=$nodename -e site=$site -e kubelet_port=$kubelet_port -e account=$account`)
- Use the `jlabtsai/jrm-fw:latest` image

## Usage

To use this script, simply run it in a bash shell:

```bash
./main.sh
```

## Note
- `/fw/my_launchpad.yaml` is the yaml file for the launchpad. You can modify it to change the launchpad settings.
- Make sure that the port of mongodb (27017 as default) is reachable for the container. If not reachable, check the port is opened to all interfaces or not. 

## Setup on db server
- Setup the db and user that are used in `my_launchpad.yaml` file. Use `FireWorks/util/create_db.sh` script to create the db and user.

## Setup on compute node
- Setup python environment based on the `requirements.txt` file.
- Setup configuration files using `FireWorks/util/create_project.py` script. This will create two files `my_qadapter.yaml` and `my_fworker.yaml`.
- Make sure that the mongodb is reachable from the compute node. If not, you can use ssh tunneling to connect to the mongodb.
