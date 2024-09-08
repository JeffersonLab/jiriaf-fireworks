apptainer exec --env SLURM_CONF=$HOME/slurm.conf --bind /run/munge/munge.socket.2:/run/munge/munge.socket.2 fw-agent_main.sif bash

shifter --image=jlabtsai/fw-agent:main --env=SLURM_CONF=$HOME/slurm.conf  -- bash

