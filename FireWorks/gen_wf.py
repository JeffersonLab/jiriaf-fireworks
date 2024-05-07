from fireworks import Workflow, Firework, LaunchPad, ScriptTask, TemplateWriterTask
import os
import time
from monty.serialization import loadfn

LPAD = LaunchPad.from_file('/fw/util/my_launchpad.yaml')

class Slurm:
    def __init__(self, config_file="/fw/node-config.yaml"):
        self.node_config = loadfn(config_file) if config_file else {}
        if not self.node_config:
            raise ValueError("node-config.yaml is empty")
        self.nnode = self.node_config["slurm"]["nnodes"]
        self.qos = self.node_config["slurm"]["qos"]
        self.walltime = self.node_config["slurm"]["walltime"]
        self.account = self.node_config["slurm"]["account"]
        self.nodetype = self.node_config["slurm"]["nodetype"]

class Jrm:
    def __init__(self, config_file="/fw/node-config.yaml"):
        self.node_config = loadfn(config_file) if config_file else {}
        if not self.node_config:
            raise ValueError("node-config.yaml is empty")
        self.control_plane_ip = self.node_config["jrm"]["control_plane_ip"]
        self.apiserver_port = self.node_config["jrm"]["apiserver_port"]
        self.nodename = self.node_config["jrm"]["nodename"]
        self.kubeconfig = self.node_config["jrm"]["kubeconfig"]
        self.vkubelet_pod_ip = self.node_config["jrm"]["vkubelet_pod_ip"]
        self.kubelet_port = self.node_config["jrm"]["kubelet_port"]
        self.site = self.node_config["jrm"]["site"]
        self.image = self.node_config["jrm"]["image"]

class Ssh:
    def __init__(self, config_file="/fw/node-config.yaml"):
        self.node_config = loadfn(config_file) if config_file else {}
        if not self.node_config:
            raise ValueError("node-config.yaml is empty")
        self.apiserver = self.node_config["ssh"]["apiserver"]
        self.metrics_server = self.node_config["ssh"]["metrics_server"]


def launch_jrm_script():
    slurm = Slurm()
    jrm = Jrm()
    ssh = Ssh()
    
    # translate walltime to seconds, eg 01:00:00 -> 3600
    jrm_walltime = sum(int(x) * 60 ** i for i, x in enumerate(reversed(slurm.walltime.split(":"))))

    script = f"""
    #!/bin/bash

    export NODENAME={jrm.nodename}
    export KUBECONFIG={jrm.kubeconfig}
    export VKUBELET_POD_IP={jrm.vkubelet_pod_ip}
    export KUBELET_PORT={jrm.kubelet_port}
    export JIRIAF_WALLTIME={jrm_walltime}
    export JIRIAF_NODETYPE={slurm.nodetype}
    export JIRIAF_SITE={jrm.site}

    echo JRM: $NODENAME is running on $HOSTNAME
    echo Walltime: $JIRIAF_WALLTIME, nodetype: $JIRIAF_NODETYPE, site: $JIRIAF_SITE

    ssh -NfL {jrm.apiserver_port}:localhost:{jrm.apiserver_port} {ssh.apiserver}
    ssh -NfR {jrm.kubelet_port}:localhost:{jrm.kubelet_port} {ssh.metrics_server}

    shifter --image={jrm.image} -- /bin/bash -c "cp -r /vk-cmd `pwd`/vk-cmd"
    cd `pwd`/vk-cmd

    echo api-server: {jrm.apiserver_port}, kubelet: {jrm.kubelet_port}

    ./start.sh $KUBECONFIG $NODENAME $VKUBELET_POD_IP $KUBELET_PORT $JIRIAF_WALLTIME $JIRIAF_NODETYPE $JIRIAF_SITE
    """

    task1 = f"echo '{script}' > jrm.sh"
    task2 = "chmod +x jrm.sh"
    task3 = "./jrm.sh"

    tasks = [ScriptTask.from_str(task1), ScriptTask.from_str(task2), ScriptTask.from_str(task3)]

    fw = Firework(tasks, name=f"{jrm.site}_{jrm.nodename}")
    fw.spec["_category"] = jrm.site
    fw.spec["_queueadapter"] = {
        "job_name": f"{jrm.site}_{jrm.nodename}",
        "walltime": slurm.walltime,
        "qos": slurm.qos,
        "nodes": slurm.nnode,
        "account": slurm.account,
        "constraint": slurm.nodetype
        }
    
    # preempt has min walltime of 2 hours (can get stop after 2 hours)
    # debug_preempt has max walltime of 30 minutes (can get stop after 5 minutes)
    wf = Workflow([fw], {fw: []})
    wf.name = f"{jrm.site}_{jrm.nodename}"
    return wf


def add_jrm():
    wf = launch_jrm_script()
    LPAD.add_wf(wf)
    print(f"Add workflow {wf.name} to LaunchPad")

if __name__ == "__main__":
    add_jrm()