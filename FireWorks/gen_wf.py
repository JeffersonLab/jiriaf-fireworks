from fireworks import Workflow, Firework, LaunchPad, ScriptTask, TemplateWriterTask
import time
from monty.serialization import loadfn
import textwrap

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


class Task:
    def __init__(self, slurm_instance, jrm_instance, ssh_instance):
        self.slurm = slurm_instance
        self.jrm = jrm_instance
        self.ssh = ssh_instance

    def get_jrm_script(self, node_id, kubelet_port):
        # translate walltime to seconds, eg 01:00:00 -> 3600
        jrm_walltime = sum(int(x) * 60 ** i for i, x in enumerate(reversed(self.slurm.walltime.split(":"))))
        nodename = f"{self.jrm.nodename}-{node_id}"

        script = textwrap.dedent(f"""
            #!/bin/bash

            export NODENAME={nodename}
            export KUBECONFIG={self.jrm.kubeconfig}
            export VKUBELET_POD_IP={self.jrm.vkubelet_pod_ip}
            export KUBELET_PORT={kubelet_port}
            export JIRIAF_WALLTIME={jrm_walltime}
            export JIRIAF_NODETYPE={self.slurm.nodetype}
            export JIRIAF_SITE={self.jrm.site}

            echo JRM: \$NODENAME is running on \$HOSTNAME
            echo Walltime: \$JIRIAF_WALLTIME, nodetype: \$JIRIAF_NODETYPE, site: \$JIRIAF_SITE

            ssh -NfL {self.jrm.apiserver_port}:localhost:{self.jrm.apiserver_port} {self.ssh.apiserver}
            ssh -NfR {kubelet_port}:localhost:{kubelet_port} {self.ssh.metrics_server}

            shifter --image={self.jrm.image} -- /bin/bash -c "cp -r /vk-cmd `pwd`/{nodename}"
            cd `pwd`/{nodename}

            echo api-server: {self.jrm.apiserver_port}, kubelet: {kubelet_port}

            ./start.sh \$KUBECONFIG \$NODENAME \$VKUBELET_POD_IP \$KUBELET_PORT \$JIRIAF_WALLTIME \$JIRIAF_NODETYPE \$JIRIAF_SITE
        """)

        # Now, `script` contains the bash script with correct indentation.
        return script, nodename


def launch_jrm_script():
    slurm = Slurm()
    jrm = Jrm()
    ssh = Ssh()
    
    task = Task(slurm, jrm, ssh)

    tasks, nodenames = [], []
    for port in range(slurm.nnode):
        # unique timestamp for each node
        timestamp = str(int(time.time()))
        script, nodename = task.get_jrm_script(timestamp, 10000+port) # kubelet port starts from 10000; this is not good!
        nodenames.append(nodename)

        tasks.append(ScriptTask.from_str(f"cat << EOF > {nodename}.sh\n{script}\nEOF"))
        tasks.append(ScriptTask.from_str(f"chmod +x {nodename}.sh"))
        # tasks.append(ScriptTask.from_str(f"srun --nodes=1 sh {nodename}.sh& wait; echo 'Node {nodename} is done'"))
        # sleep 1 second
        time.sleep(1)

    exec_task = ScriptTask.from_str(f"for nodename in {' '.join(nodenames)}; do srun --nodes=1 sh $nodename.sh& done; wait; echo 'All nodes are done'")
    tasks.append(exec_task)

    fw = Firework(tasks, name=f"{jrm.site}_{nodename}")
    fw.spec["_category"] = jrm.site
    fw.spec["_queueadapter"] = {
        "job_name": f"{jrm.site}_{nodename}",
        "walltime": slurm.walltime,
        "qos": slurm.qos,
        "nodes": slurm.nnode,
        "account": slurm.account,
        "constraint": slurm.nodetype
        }
    
    # preempt has min walltime of 2 hours (can get stop after 2 hours)
    # debug_preempt has max walltime of 30 minutes (can get stop after 5 minutes)
    wf = Workflow([fw], {fw: []})
    wf.name = f"{jrm.site}_{nodename}"
    return wf


def add_jrm():
    wf = launch_jrm_script()
    LPAD.add_wf(wf)
    print(f"Add workflow {wf.name} to LaunchPad")

if __name__ == "__main__":
    add_jrm()