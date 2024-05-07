#!/bin/bash

# Reset environment variables
unset nnodes nodetype walltime account nodename site kubelet_port

# Check if environment variables are set
if [ -z "$nnodes" ] || [ -z "$nodetype" ] || [ -z "$walltime" ] || [ -z "$account" ] || [ -z "$nodename" ] || [ -z "$site" ] || [ -z "$kubelet_port" ]; then
    echo "One or more environment variables are not set. Please set the following variables: nnodes, nodetype, walltime, account, nodename, site, kubelet_port."
    exit 1
fi

cat << EOF > /fw/node-config.yaml
slurm:
    nnodes: ${nnodes}
    nodetype: ${nodetype}
    walltime: ${walltime}
    qos: debug
    account: ${account} #m4637 - jiriaf or m3792 - nersc

jrm:
    nodename: ${nodename}
    site: ${site}
    
    control_plane_ip: jiriaf2301
    apiserver_port: 35679
    kubeconfig: /global/homes/j/jlabtsai/config/kubeconfig
    vkubelet_pod_ip: "172.17.0.1"
    kubelet_port: ${kubelet_port}
    image: docker:jlabtsai/vk-cmd:main

ssh:
    apiserver: login04
    metrics_server: login04
EOF

