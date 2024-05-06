#!/bin/bash

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

