import textwrap
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import time

class SiteStrategy:
    def __init__(self, task_manager):
        self.task_manager = task_manager

    def get_remote_ssh_cmds(self, nodename, available_kubelet_ports, available_custom_metrics_ports):
        kubelet_port = available_kubelet_ports.get()  # Get a port from the queue
        self.task_manager.jrm_ports.append(kubelet_port)

        commands = [
            self.build_ssh_command(self.task_manager.jrm.apiserver_port, reverse=False),
            self.build_ssh_command(kubelet_port, reverse=True)
        ]

        cmd = self.task_manager.ssh.connect_metrics_server(kubelet_port, nodename)
        self.task_manager.ssh_metrics_cmds.append(cmd)
        print(f"Node {nodename} is running on port {kubelet_port}")

        # Handle custom metrics ports
        if self.task_manager.jrm.custom_metrics_ports:
            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(self.execute_custom_metric_command, port, nodename, available_custom_metrics_ports)
                    for port in self.task_manager.jrm.custom_metrics_ports
                ]
                for future in as_completed(futures):
                    commands.append(future.result())

        return "; ".join(commands), kubelet_port

    def build_ssh_command(self, port, reverse, remote_port=None):
        """
        Build SSH command, with an optional remote_port parameter for reverse SSH tunnels.
        """
        raise NotImplementedError("Subclasses should implement this method to generate SSH commands.")

    def execute_custom_metric_command(self, port, nodename, available_custom_metrics_ports):
        mapped_port = available_custom_metrics_ports.get()  # Get a port from the queue
        command = self.build_ssh_command(mapped_port, reverse=True, remote_port=port)
        self.task_manager.dict_mapped_custom_metrics_ports[mapped_port] = port
        cmd = self.task_manager.ssh.connect_custom_metrics(mapped_port, port, nodename)
        self.task_manager.ssh_custom_metrics_cmds.append(cmd)
        print(f"Node {nodename} is exposing custom metrics port {port} on port {mapped_port}")
        return command

    def get_jrm_script(self, nodename, kubelet_port, ssh_cmds, vkubelet_pod_ip):
        jrm_walltime = sum(int(x) * 60 ** i for i, x in enumerate(reversed(self.task_manager.slurm.walltime.split(":"))))
        container_command = self.build_container_command(nodename)

        script = textwrap.dedent(f"""
            #!/bin/bash -l

            export NODENAME={nodename}
            export KUBECONFIG={self.task_manager.jrm.kubeconfig}
            export VKUBELET_POD_IP={vkubelet_pod_ip}
            export KUBELET_PORT={kubelet_port}
            export JIRIAF_WALLTIME={jrm_walltime}
            export JIRIAF_NODETYPE={self.task_manager.slurm.constraint}
            export JIRIAF_SITE={self.task_manager.jrm.site}

            echo JRM: $NODENAME is running on $HOSTNAME with IP $VKUBELET_POD_IP and port $KUBELET_PORT
            echo Walltime: $JIRIAF_WALLTIME seconds, nodetype: $JIRIAF_NODETYPE, site: $JIRIAF_SITE

            {ssh_cmds}

            {container_command}
            cd `pwd`/{nodename}

            echo api-server: {self.task_manager.jrm.apiserver_port}, kubelet: {kubelet_port}

            ./start.sh $KUBECONFIG $NODENAME $VKUBELET_POD_IP $KUBELET_PORT $JIRIAF_WALLTIME $JIRIAF_NODETYPE $JIRIAF_SITE &

            # sleep \$JIRIAF_WALLTIME
            sleep $(echo $(squeue -h -j $SLURM_JOB_ID -o %L) | awk -F '[-:]' '{{if (NF==4) {{print ($1*86400) + ($2*3600) + ($3*60) + $4}} else if (NF==3) {{print ($1*3600) + ($2*60) + $3}} else {{print ($1*60) + $2}}}}')
            # echo "Walltime \$JIRIAF_WALLTIME is up. Stop the processes."
            pkill -f "./start.sh"
        """)
        return script

    def build_container_command(self, nodename):
        raise NotImplementedError("Subclasses should implement this method to generate container commands.")

class PerlmutterStrategy(SiteStrategy):
    def build_ssh_command(self, port, reverse, remote_port=None):
        if reverse:
            remote_port = remote_port or port  # Use remote_port if provided, otherwise fall back to port
            return f"ssh -NfR {port}:localhost:{remote_port} {self.task_manager.ssh.remote}"
        else:
            return f"ssh -NfL {port}:localhost:{port} {self.task_manager.ssh.remote}"

    def build_container_command(self, nodename):
        return f"shifter --image={self.task_manager.jrm.image} -- /bin/bash -c \"cp -r /vk-cmd `pwd`/{nodename}\""

class OrnlStrategy(SiteStrategy):
    def build_ssh_command(self, port, reverse, remote_port=None):
        decoded_password = base64.b64decode(self.task_manager.ssh.password).decode('utf-8')
        if reverse:
            remote_port = remote_port or port  # Use remote_port if provided, otherwise fall back to port
            return f"expect -c 'spawn ssh -NfR {port}:localhost:{remote_port} {self.task_manager.ssh.remote}; expect \"Password:\"; send \"{decoded_password}\\r\"; expect eof'"
        else:
            return f"expect -c 'spawn ssh -NfL {port}:localhost:{port} {self.task_manager.ssh.remote}; expect \"Password:\"; send \"{decoded_password}\\r\"; expect eof'"

    def build_container_command(self, nodename):
        return f"apptainer exec $HOME/vk-cmd_main.sif cp -r /vk-cmd `pwd`/{nodename}"

class TaskManager:
    def __init__(self, slurm_instance, jrm_instance, ssh_instance):
        self.slurm = slurm_instance
        self.jrm = jrm_instance
        self.ssh = ssh_instance
        self.strategy = self.get_site_strategy(jrm_instance.site)

        self.jrm_ports = []
        self.dict_mapped_custom_metrics_ports = {}
        self.ssh_metrics_cmds = []
        self.ssh_custom_metrics_cmds = []

    def get_site_strategy(self, site_type):
        if site_type == "perlmutter":
            return PerlmutterStrategy(self) # Pass TaskManager instance to the strategy
        elif site_type == "ornl":
            return OrnlStrategy(self) # Pass TaskManager instance to the strategy
        else:
            raise ValueError(f"Unsupported site type: {site_type}")

    def get_remote_ssh_cmds(self, nodename, available_kubelet_ports, available_custom_metrics_ports):
        return self.strategy.get_remote_ssh_cmds(nodename, available_kubelet_ports, available_custom_metrics_ports)

    def get_jrm_script(self, nodename, kubelet_port, ssh_cmds, vkubelet_pod_ip):
        return self.strategy.get_jrm_script(nodename, kubelet_port, ssh_cmds, vkubelet_pod_ip)
