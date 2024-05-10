# JRM Deployment Guide

Follow the steps below to run the JRM deployment:

## Step 1: Create SSH Connections

Run the `jrm-create-ssh-connections` binary. It is an HTTP server that listens on port 8888. This creates SSH connections (db port, apiserver port, and jrm port) for the JRMs.

Here's what it does:

1. Looks for available ports from 10000 to 19999 on localhost.
2. Runs the commands from `FireWorks/gen_wf.py` to create SSH connections.

**Note:** It considers listening ports as NOT available. So, ensure to delete ports that are not in use anymore when deleting JRMs. (check database for the ports used by JRMs.)

For more details, check the `create-ssh-connections/jrm-fw-create-ssh-connections.go` file.

## Step 2: Set Up and Run Docker Container

Run the `main.sh` script. This sets up and runs a Docker container for launching Slurm jobs for deploying JRMs.

Check `FireWorks/create_config.sh` for the required environment variables.