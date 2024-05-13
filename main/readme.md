# JRM Deployment Guide

Follow the steps below to run the JRM deployment:

## Prerequisites
One must have a NERSC account and have set up the private key (e.g. `~/.ssh/nersc`) for log into Perlmutter. This is due to the fact that the we set up three SSH connections to Perlmutter from the local machine.
1. Connect to FireWorks MongoDB database.
```python
cmd = f"ssh -i ~/.ssh/nersc -J {self.remote_proxy} -NfR 27017:localhost:27017 {self.remote}" 
```
2. Connect to the K8s API server.
```python
cmd = f"ssh -i ~/.ssh/nersc -J {self.remote_proxy} -NfR {apiserver_port}:localhost:{apiserver_port} {self.remote}" 
```
3. Connect to the JRM for metrics of the JRM.
```python
cmd = f"ssh -i ~/.ssh/nersc -J {self.remote_proxy} -NfL *:{kubelet_port}:localhost:{kubelet_port} {self.remote}" 
```

## Step 1: Create SSH Connections

Run the `jrm-create-ssh-connections` binary. It is an HTTP server that listens on port `8888`. This creates SSH connections (db port, apiserver port, and jrm port) as shown in the prerequisites for the JRM deployment.

Here's what it does:

1. Looks for available ports from `10000` to `19999` on localhost.
2. Runs the commands from `FireWorks/gen_wf.py` to create SSH connections.

**Note:** It considers listening ports as NOT available. So, ensure to delete ports that are not in use anymore when deleting JRMs. (One can identify the ports by checking the database and searching for the Completed fireworks.) -> Todo: Add a feature to delete the ports.

For more details, check the `create-ssh-connections/jrm-fw-create-ssh-connections.go` file.

## Step 2: Configure Environment Variables
The `main.sh` script is responsible for initializing the environment variables required to launch JRMs. It sets the following variables:

- `nnodes`: This represents the number of nodes.
- `nodetype`: This defines the type of node.
- `walltime`: This is the walltime allocated for the slurm job and JRM.
- `nodename`: This is the name assigned to the node.
- `site`: This is the site name.
- `account`: This is the account number used for allocation at NERSC.

The script also creates a directory at `$HOME/jrm-launch/logs` to store logs. The path to this directory is saved in the `logs` environment variable.

If one needs to alter these environment variables, one can do so by modifying the `FireWorks/gen_wf.py` and `FireWorks/create_config.sh` files.

## Step 3: Execute the Script
Pull the docker image `jlabtsai/jrm-fw:latest` from Docker Hub. This image is used to run the JRM deployment. Execute the `main.sh` script. This script sets up and initiates a Docker container, which is used to launch Slurm jobs for deploying JRMs. The script accepts the following arguments:

1. `add_wf`: This argument adds a JRM workflow to the FireWorks database.
2. `get_wf`: This argument retrieves the table of workflows from the FireWorks database.
3. `delete_wf`: This argument removes a specific workflow from the FireWorks database.


# Walltime Discrepancy Between JRM and Slurm Job
The `JIRIAF_WALLTIME` variable in `FireWorks/gen_wf.py` is intentionally set to be `60 seconds` less than the walltime of the Slurm job. This is to ensure that the JRM has enough time to initialize and start running. 

Once `JIRIAF_WALLTIME` expires, the JRM will be terminated. The commands for tracking the walltime and terminating the JRM are explicitly defined in the `FireWorks/gen_wf.py` file, as shown below:

```bash
sleep $JIRIAF_WALLTIME
echo "Walltime $JIRIAF_WALLTIME has ended. Terminating the processes."
pkill -f "./start.sh"