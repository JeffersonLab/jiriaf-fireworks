1. Run `setup-ssh-at-apiserver.sh` to set up the SSH connections between the API server and the JRM.
2. Run `delete-notready-jrm.sh` to delete the JRMs with the status 'notready'.
3. Run `main.sh` to set up and run a Docker container for launching Slurm jobs for deploying JRMs.