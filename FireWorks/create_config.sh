#!/bin/bash

# Check if each variable is set and print a message if it's not
if [ -z "$nnodes" ]; then
    echo "The nnodes variable is not set."
    exit 1
fi
if [ -z "$nodetype" ]; then
    echo "The nodetype variable is not set."
    exit 1
fi
if [ -z "$walltime" ]; then
    echo "The walltime variable is not set."
    exit 1
fi
if [ -z "$account" ]; then
    echo "The account variable is not set."
    exit 1
fi
if [ -z "$nodename" ]; then
    echo "The nodename variable is not set."
    exit 1
fi
if [ -z "$site" ]; then
    echo "The site variable is not set."
    exit 1
fi
if [ -z "$control_plane_ip" ]; then
    echo "The control_plane_ip variable is not set."
    exit 1
fi
if [ -z "$apiserver_port" ]; then
    echo "The apiserver_port variable is not set."
    exit 1
fi
if [ -z "$kubeconfig" ]; then
    echo "The kubeconfig variable is not set."
    exit 1
fi
if [ -z "$ssh_key" ]; then
    echo "The ssh_key variable is not set."
    exit 1
fi
if [ -z "$ssh_remote" ]; then
    echo "The ssh_remote variable is not set."
    exit 1
fi
if [ -z "$ssh_remote_proxy" ]; then
    echo "The ssh_remote_proxy variable is not set."
    exit 1
fi

# Convert the space-separated string into a YAML list if it's set and not an empty string
if [ -n "$custom_metrics_ports" ] && [ "$custom_metrics_ports" != "" ]; then
    custom_metrics_ports_yaml=$(for port in $custom_metrics_ports; do echo "    - $port"; done)
    custom_metrics_ports_yaml="custom_metrics_ports: 
$custom_metrics_ports_yaml"
else
    custom_metrics_ports_yaml=""
fi

cat << EOF > /fw/node-config.yaml
slurm:
    nnodes: ${nnodes}
    nodetype: ${nodetype}
    walltime: ${walltime}
    qos: ${qos}
    account: ${account} #m4637 - jiriaf or m3792 - nersc

jrm:
    nodename: ${nodename}
    site: ${site}
    
    control_plane_ip: ${control_plane_ip}  #jiriaf2301
    apiserver_port: ${apiserver_port} #35679
    kubeconfig:  ${kubeconfig}
    vkubelet_pod_ip: ${vkubelet_pod_ip}
    image: ${jrm_image}

    $custom_metrics_ports_yaml

ssh:
    remote_proxy: ${ssh_remote_proxy}
    remote: ${ssh_remote}
    ssh_key: ${ssh_key}
EOF

cp /fw/node-config.yaml /fw/logs/${nodename}_node-config.yaml