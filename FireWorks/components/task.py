import textwrap
import base64
import concurrent.futures

class TaskManager:
    def __init__(self, slurm_instance, jrm_instance, ssh_instance, site_type="perlmutter"):
        self.slurm = slurm_instance
        self.jrm = jrm_instance
        self.ssh = ssh_instance
        self.site_type = site_type

        self.jrm_ports = []
        self.dict_mapped_custom_metrics_ports = {}
        self.ssh_metrics_cmds = []
        self.ssh_custom_metrics_cmds = []

    def get_remote_ssh_cmds(self, nodename, available_kubelet_ports, available_custom_metrics_ports):
        """
        This function does three things:
        1. Requests available ports for kubelet and custom metrics ports.
        2. Creates and returns SSH tunneling commands for the remote server, including apiserver port, kubelet port, and custom metrics ports.
        3. Runs SSH tunneling commands on the local server, including kubelet port and custom metrics ports.
        """

        # Get the smallest available port for kubelet
        kubelet_port = available_kubelet_ports[0]
        # Update the available ports
        available_kubelet_ports.remove(kubelet_port)
        self.jrm_ports.append(kubelet_port)

        commands = []
        if self.site_type == "perlmutter":
            commands.append(f"ssh -NfL {self.jrm.apiserver_port}:localhost:{self.jrm.apiserver_port} {self.ssh.base_ssh.remote}")
            commands.append(f"ssh -NfR {kubelet_port}:localhost:{kubelet_port} {self.ssh.base_ssh.remote}")
        elif self.site_type == "ornl":
            decoded_password = base64.b64decode(self.ssh.base_ssh.password).decode('utf-8')
            commands.append(f"expect -c 'spawn ssh -NfL {self.jrm.apiserver_port}:localhost:{self.jrm.apiserver_port} {self.ssh.base_ssh.remote}; expect \"Password:\"; send \"{decoded_password}\\r\"; expect eof'")
            commands.append(f"expect -c 'spawn ssh -NfR {kubelet_port}:localhost:{kubelet_port} {self.ssh.base_ssh.remote}; expect \"Password:\"; send \"{decoded_password}\\r\"; expect eof'")

        cmd = self.ssh.connect_metrics_server(kubelet_port, nodename)
        self.ssh_metrics_cmds.append(cmd)
        print(f"Node {nodename} is running on port {kubelet_port}")

        # Function to handle SSH command execution
        def execute_ssh_command(ssh, port, nodename):
            mapped_port = available_custom_metrics_ports[0]
            available_custom_metrics_ports.remove(mapped_port)

            if self.site_type == "perlmutter":
                command = f"ssh -NfR {mapped_port}:localhost:{port} {ssh.base_ssh.remote}"
            elif self.site_type == "ornl":
                command = f"expect -c 'spawn ssh -NfR {mapped_port}:localhost:{port} {ssh.base_ssh.remote}; expect \"Password:\"; send \"{decoded_password}\\r\"; expect eof'"

            self.dict_mapped_custom_metrics_ports[mapped_port] = port
            cmd = ssh.connect_custom_metrics(mapped_port, port, nodename)
            self.ssh_custom_metrics_cmds.append(cmd)
            print(f"Node {nodename} is exposing custom metrics port {port} on port {mapped_port}")
            return command

        # If custom metrics ports are defined
        if self.jrm.custom_metrics_ports:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(execute_ssh_command, self.ssh, port, nodename) for port in self.jrm.custom_metrics_ports]
                for future in concurrent.futures.as_completed(futures):
                    commands.append(future.result())

        return "; ".join(commands), kubelet_port

    def get_jrm_script(self, nodename, kubelet_port, ssh_cmds, vkubelet_pod_ip):
        # Translate walltime to seconds, eg 01:00:00 -> 3600
        jrm_walltime = sum(int(x) * 60 ** i for i, x in enumerate(reversed(self.slurm.walltime.split(":"))))
        # JRM needs 1 min to warm up. Subtract 1*60 from jrm_walltime.
        jrm_walltime -= 1 * 60

        if self.site_type == "perlmutter":
            container_command = f"shifter --image={self.jrm.image} -- /bin/bash -c \"cp -r /vk-cmd `pwd`/{nodename}\""
        elif self.site_type == "ornl":
            container_command = f"apptainer exec $HOME/vk-cmd_main.sif cp -r /vk-cmd `pwd`/{nodename}"

        script = textwrap.dedent(f"""
            #!/bin/bash -l

            export NODENAME={nodename}
            export KUBECONFIG={self.jrm.kubeconfig}
            export VKUBELET_POD_IP={vkubelet_pod_ip}
            export KUBELET_PORT={kubelet_port}
            export JIRIAF_WALLTIME={jrm_walltime}
            export JIRIAF_NODETYPE={self.slurm.constraint}
            export JIRIAF_SITE={self.jrm.site}

            echo JRM: \$NODENAME is running on \$HOSTNAME with IP \$VKUBELET_POD_IP and port \$KUBELET_PORT
            echo Walltime: \$JIRIAF_WALLTIME, nodetype: \$JIRIAF_NODETYPE, site: \$JIRIAF_SITE

            {ssh_cmds}

            {container_command}
            cd `pwd`/{nodename}

            echo api-server: {self.jrm.apiserver_port}, kubelet: {kubelet_port}

            ./start.sh \$KUBECONFIG \$NODENAME \$VKUBELET_POD_IP \$KUBELET_PORT \$JIRIAF_WALLTIME \$JIRIAF_NODETYPE \$JIRIAF_SITE &

            # Stop the processes after the walltime. This is essential for making sure the firework is completed.
            sleep \$JIRIAF_WALLTIME
            echo "Walltime \$JIRIAF_WALLTIME is up. Stop the processes."
            pkill -f "./start.sh"

        """)

        return script
