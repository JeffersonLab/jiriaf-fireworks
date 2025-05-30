import textwrap
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import time

from site_config import get_site_config

class TaskManager:
    def __init__(self, slurm_instance, jrm_instance, ssh_instance):
        self.slurm = slurm_instance
        self.jrm = jrm_instance
        self.ssh = ssh_instance
        self.site_config = get_site_config(jrm_instance.config_class if jrm_instance.config_class else jrm_instance.site)
        self.site_config.set_managers(self, ssh_instance)

        self.jrm_ports = []
        self.dict_mapped_custom_metrics_ports = {}
        self.ssh_metrics_cmds = []
        self.ssh_custom_metrics_cmds = []

        self.jrm.site = jrm_instance.site  # Ensure the correct site is used for JIRIAF_SITE

    def setup_ssh_connections(self, nodename, available_kubelet_ports, available_custom_metrics_ports):
        kubelet_port = available_kubelet_ports.get()  # Get a port from the queue
        self.jrm_ports.append(kubelet_port)

        commands = [
            self.site_config.setup_remote_ssh_cmd(self.jrm.apiserver_port, reverse=False),
            self.site_config.setup_remote_ssh_cmd(kubelet_port, reverse=True)
        ]

        metrics_response = self.ssh.connect_metrics_server(kubelet_port, nodename)
        if "error" in metrics_response:
            print(f"Error in connecting metrics server for node {nodename}: {metrics_response['error']}")
            return None, None
        self.ssh_metrics_cmds.append(metrics_response)
        print(f"Node {nodename} is running on port {kubelet_port}")

        # Handle custom metrics ports
        if self.jrm.custom_metrics_ports:
            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(self.execute_custom_metric_command, port, nodename, available_custom_metrics_ports)
                    for port in self.jrm.custom_metrics_ports
                ]
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result is None:  # If execute_custom_metric_command returned None due to error
                            print(f"Error in setting up custom metrics for node {nodename}")
                            return None, None
                        commands.append(result)
                    except Exception as e:
                        print(f"Error in setting up custom metrics for node {nodename}: {str(e)}")
                        return None, None

        ssh_remote_commands = "echo 'no ssh remote commands'" if all(cmd == "" for cmd in commands) else "; ".join(commands)
        return ssh_remote_commands, kubelet_port

    def execute_custom_metric_command(self, port, nodename, available_custom_metrics_ports):
        mapped_port = available_custom_metrics_ports.get()  # Get a port from the queue
        command = self.site_config.setup_remote_ssh_cmd(mapped_port, reverse=True, remote_port=port)
        self.dict_mapped_custom_metrics_ports[mapped_port] = port
        response = self.ssh.connect_custom_metrics(mapped_port, port, nodename)
        if "error" in response:
            print(f"Error in connecting custom metrics for node {nodename} on port {port}: {response['error']}")
            return None
        self.ssh_custom_metrics_cmds.append(response)
        print(f"Node {nodename} is exposing custom metrics port {port} on port {mapped_port}")
        return command

    def get_jrm_script(self, nodename, kubelet_port, ssh_cmds, vkubelet_pod_ip):
        jrm_walltime = sum(int(x) * 60 ** i for i, x in enumerate(reversed(self.slurm.walltime.split(":")))) if self.slurm.walltime else 0
        container_command = self.site_config.build_container_command(nodename)

        script = textwrap.dedent(f"""
            #!/bin/bash -l

            export NODENAME={nodename}
            export KUBECONFIG={self.jrm.kubeconfig}
            export VKUBELET_POD_IP={vkubelet_pod_ip}
            export KUBELET_PORT={kubelet_port}
            export JIRIAF_WALLTIME={jrm_walltime}
            export JIRIAF_NODETYPE={self.slurm.constraint}
            export JIRIAF_SITE={self.jrm.site}

            echo JRM: $NODENAME is running on $HOSTNAME with IP $VKUBELET_POD_IP and port $KUBELET_PORT
            echo Walltime: $JIRIAF_WALLTIME seconds, nodetype: $JIRIAF_NODETYPE, site: $JIRIAF_SITE

            {ssh_cmds}

            {container_command}
            cd `pwd`/{nodename}

            echo api-server: {self.jrm.apiserver_port}, kubelet: {kubelet_port}

            ./start.sh $KUBECONFIG $NODENAME $VKUBELET_POD_IP $KUBELET_PORT $JIRIAF_WALLTIME $JIRIAF_NODETYPE $JIRIAF_SITE &

            
            if [ "$JIRIAF_WALLTIME" -eq 0 ]; then
                # Keep the script alive indefinitely
                while true; do
                    sleep 3600  # Sleep for an hour and then check again
                done
            else
                sleep $(echo $(squeue -h -j $SLURM_JOB_ID -o %L) | awk -F '[-:]' '{{if (NF==4) {{print ($1*86400) + ($2*3600) + ($3*60) + $4}} else if (NF==3) {{print ($1*3600) + ($2*60) + $3}} else {{print ($1*60) + $2}}}}')
                pkill -f "./start.sh"
            fi
        """)
        return script
