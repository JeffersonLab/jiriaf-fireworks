# README.md

## Overview

The `main/main.sh` script is a bash script that sets up and runs a Docker container. This container launches Slurm jobs for deploying JRMs. The script sets several environment variables and then runs a Docker container with specific settings.

## Environment Variables

The script sets the following environment variables:

- `nnodes`: Number of nodes.
- `nodetype`: Type of node.
- `walltime`: Walltime for the slurm job and JRM.
- `nodename`: Name of the node.
- `site`: Site name.
- `account`: Account number for the allocation at NERSC.

## Log Directory

The script creates a directory at `$HOME/jrm-launch/logs` for storing logs. The path to this directory is stored in the `logs` environment variable.

## Docker Run

The script runs a Docker container with the following settings:

- Mounts the log directory to `/fw/logs` in the container (`-v $log:/fw/logs`).
- Sets the environment variables inside the container (`-e nnodes=$nnodes -e nodetype=$nodetype -e walltime=$walltime -e nodename=$nodename -e site=$site -e account=$account`).
- Uses the `jlabtsai/jrm-fw:latest` image.

## Usage

To use this script, refer to the instructions in `main/readme.md`.

## Note

- `/fw/util/my_launchpad.yaml` is the yaml file for the launchpad. Modify it to change the launchpad settings. (It is related to setting for db.)
- Ensure that the port of mongodb (27017 as default) is reachable for the container. If not, check if the port is open to all interfaces.

## Setup on db server

- Set up the db and user that are used in `my_launchpad.yaml` file. Use `FireWorks/util/create_db.sh` script to create the db and user.

## Setup on compute node

- Set up python environment based on the `requirements.txt` file.
- Set up configuration files using `FireWorks/util/create_project.py` script. This will create two files `my_qadapter.yaml` and `my_fworker.yaml`. Check the examples `FireWorks/util/my_launchpad.yaml` and `FireWorks/util/my_qadapter.yaml` files.
- Ensure that the mongodb is reachable from the compute node. If not, you can use ssh tunneling to connect to the mongodb.