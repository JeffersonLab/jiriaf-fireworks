from fireworks import Workflow, Firework, LaunchPad, ScriptTask
import time
from monty.serialization import loadfn
import textwrap
import requests, json, logging
import argparse
import concurrent.futures
import uuid


LPAD = LaunchPad.from_file('/fw/util/my_launchpad.yaml')
LOG_PATH = '/fw/logs/'

class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(f'{LOG_PATH}{name}.log')
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(self, msg):
        self.logger.debug(msg)


class Slurm:
    def __init__(self, config_file="/fw/node-config.yaml"):
        self.node_config = loadfn(config_file) if config_file else {}
        if not self.node_config:
            raise ValueError("node-config.yaml is empty")
        self.nodes = self.node_config["slurm"]["nodes"]
        self.qos = self.node_config["slurm"]["qos"]
        self.walltime = self.node_config["slurm"]["walltime"]
        self.account = self.node_config["slurm"]["account"]
        self.constraint = self.node_config["slurm"]["constraint"]
        self.reservation = self.node_config["slurm"]["reservation"] if "reservation" in self.node_config["slurm"] else None

class Jrm:
    def __init__(self, config_file="/fw/node-config.yaml"):
        self.node_config = loadfn(config_file) if config_file else {}
        if not self.node_config:
            raise ValueError("node-config.yaml is empty")
        
        self.control_plane_ip = self.node_config["jrm"]["control_plane_ip"]
        if not self.control_plane_ip:
            self.control_plane_ip = "jiriaf2301"

        self.apiserver_port = self.node_config["jrm"]["apiserver_port"]
        if not self.apiserver_port:
            self.apiserver_port = "35679"

        self.kubeconfig = self.node_config["jrm"]["kubeconfig"]
        if not self.kubeconfig:
            self.kubeconfig = "/global/homes/j/jlabtsai/config/kubeconfig"

        self.nodename = self.node_config["jrm"]["nodename"]
        self.vkubelet_pod_ips = self.node_config["jrm"]["vkubelet_pod_ips"] if "vkubelet_pod_ips" in self.node_config["jrm"] else []
    
        self.site = self.node_config["jrm"]["site"]
        if not self.site:
            self.site = "perlmutter"
        self.image = self.node_config["jrm"]["image"]
        if not self.image:
            self.image = "docker:jlabtsai/vk-cmd:main"
        self.custom_metrics_ports = self.node_config["jrm"]["custom_metrics_ports"] if "custom_metrics_ports" in self.node_config["jrm"] else []

class Ssh:
    def __init__(self, config_file="/fw/node-config.yaml"):
        self.node_config = loadfn(config_file) if config_file else {}
        if not self.node_config:
            raise ValueError("node-config.yaml is empty")
        self.remote = self.node_config["ssh"]["remote"]
        self.remote_proxy = self.node_config["ssh"]["remote_proxy"]
        self.ssh_key = self.node_config["ssh"]["ssh_key"]

    @classmethod
    def send_command(cls, command):
        url = "http://172.17.0.1:8888/run"
        data = {'command': command}
        response = requests.post(url, data=data)  # Use data instead of json
        if response.status_code == 200:
            response_text = response.text.replace('\n', '\\n')
            return json.loads(response_text)
        else:
            return None
        
    @classmethod
    def request_available_port(cls, start, end, ip="127.0.0.1"):
        url = f"http://172.17.0.1:8888/get_port/{ip}/{start}/{end}"
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    @classmethod
    def request_available_ports(cls, start, end, ip="127.0.0.1"):
        url = f"http://172.17.0.1:8888/get_ports/{ip}/{start}/{end}"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def connect_db(self):
        # send the cmd to REST API server listening 8888
        cmd = f"""
        if ! pgrep -f "ssh -i {self.ssh_key} -J {self.remote_proxy} -NfR 27017:localhost:27017 {self.remote}" > /dev/null; then
            ssh -i {self.ssh_key} -J {self.remote_proxy} -NfR 27017:localhost:27017 {self.remote}
        else
            echo "SSH command is already running."
        fi
        """
        response = Ssh.send_command(cmd)
        # write response to log
        logger = Logger('connect_db_logger')
        # add cmd to response for record
        response['cmd'] = cmd
        response["remote_proxy"] = self.remote_proxy
        response["remote"] = self.remote
        response["port"] = "27017"
        logger.log(response)
        return response


    def connect_apiserver(self, apiserver_port):
        # send the cmd to REST API server listening 8888
        cmd = f"""
        if ! pgrep -f "ssh -i {self.ssh_key} -J {self.remote_proxy} -NfR {apiserver_port}:localhost:{apiserver_port} {self.remote}" > /dev/null; then
            ssh -i {self.ssh_key} -J {self.remote_proxy} -NfR {apiserver_port}:localhost:{apiserver_port} {self.remote}
        else
            echo "SSH command is already running."
        fi
        """
        response = Ssh.send_command(cmd)
        logger = Logger('connect_apiserver_logger')
        # add cmd to response for record
        response['cmd'] = cmd
        response["remote_proxy"] = self.remote_proxy
        response["remote"] = self.remote
        response["port"] = str(apiserver_port)
        logger.log(response)
        return response
    
    def connect_metrics_server(self, kubelet_port, nodename):
        # send the cmd to REST API server listening 8888
        cmd = f"ssh -i {self.ssh_key} -J {self.remote_proxy} -NfL *:{kubelet_port}:localhost:{kubelet_port} {self.remote}" 
        response = Ssh.send_command(cmd)
        logger = Logger('connect_metrics_server_logger')
        # add cmd to response for record
        response['cmd'] = cmd
        response["remote_proxy"] = self.remote_proxy
        response["remote"] = self.remote
        response["port"] = str(kubelet_port)
        response["nodename"] = nodename
        logger.log(response)
        return response

    def connect_custom_metrics(self, mapped_port, custom_metrics_port, nodename):
        # send the cmd to REST API server listening 8888
        cmd = f"ssh -i {self.ssh_key} -J {self.remote_proxy} -NfL *:{mapped_port}:localhost:{mapped_port} {self.remote}" 
        response = Ssh.send_command(cmd)
        logger = Logger('connect_custom_metrics_logger')
        # add cmd to response for record
        response['cmd'] = cmd
        response["remote_proxy"] = self.remote_proxy
        response["remote"] = self.remote
        response["port"] = {"mapped_port": str(mapped_port), "custom_metrics_port": str(custom_metrics_port)}
        response["nodename"] = nodename
        logger.log(response)
        return response

class Task:
    def __init__(self, slurm_instance, jrm_instance, ssh_instance):
        self.slurm = slurm_instance
        self.jrm = jrm_instance
        self.ssh = ssh_instance

        self.jrm_ports = []
        self.dict_mapped_custom_metrics_ports = {}
        self.ssh_metrics_cmds = []
        self.ssh_custom_metrics_cmds = []

    def get_remote_ssh_cmds(self, nodename, available_kubelet_ports, available_custom_metrics_ports):
        """
        This function do three things:
        1. Request available port for kubelet and custom metrics ports
        2. Create and return SSH tunneling commands for the remote server, including apiserver port, kubelet port, and custom metrics ports.
        3. Run SSH tunneling commands on the local server, including kubelet port and custom metrics ports.
        """

    
        # get the smallest available port for kubelet
        kubelet_port = available_kubelet_ports[0]
        # update the available ports
        available_kubelet_ports.remove(kubelet_port)
        self.jrm_ports.append(kubelet_port)

      
        commands = []
        commands.append(f"ssh -NfL {self.jrm.apiserver_port}:localhost:{self.jrm.apiserver_port} {self.ssh.remote}")
        commands.append(f"ssh -NfR {kubelet_port}:localhost:{kubelet_port} {self.ssh.remote}")
        
        cmd = self.ssh.connect_metrics_server(kubelet_port, nodename)
        self.ssh_metrics_cmds.append(cmd)
        print(f"Node {nodename} is running on port {kubelet_port}")
        # time.sleep(1)

        
        # Function to handle SSH command execution
        def execute_ssh_command(ssh, port, nodename):
            mapped_port = available_custom_metrics_ports[0]
            available_custom_metrics_ports.remove(mapped_port)

            command = f"ssh -NfR {mapped_port}:localhost:{port} {ssh.remote}"
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
                    # time.sleep(1)
                        
        return "; ".join(commands), kubelet_port

    def get_jrm_script(self, nodename, kubelet_port, ssh_cmds, vkubelet_pod_ip):
        # translate walltime to seconds, eg 01:00:00 -> 3600
        jrm_walltime = sum(int(x) * 60 ** i for i, x in enumerate(reversed(self.slurm.walltime.split(":"))))
        # jrm need 1 min to warm up. substract 1*60 from jrm_walltime.
        jrm_walltime -= 1 * 60

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

            shifter --image={self.jrm.image} -- /bin/bash -c "cp -r /vk-cmd `pwd`/{nodename}"
            cd `pwd`/{nodename}

            echo api-server: {self.jrm.apiserver_port}, kubelet: {kubelet_port}

            ./start.sh \$KUBECONFIG \$NODENAME \$VKUBELET_POD_IP \$KUBELET_PORT \$JIRIAF_WALLTIME \$JIRIAF_NODETYPE \$JIRIAF_SITE &

            # stop the processes after the walltim. this is essential for making sure the firework is completed.
            sleep \$JIRIAF_WALLTIME
            echo "Walltime \$JIRIAF_WALLTIME is up. Stop the processes."
            pkill -f "./start.sh"

        """)

        # Now, `script` contains the bash script with correct indentation.
        return script

class MangagePorts:
    # inherit from Ssh class
    def __init__(self):
        super().__init__()
        self.to_delete_ports = []
        self.to_delete_fw_ids = []
        self.to_delete_knodes = []


    def find_ports_from_lpad(self, lost_runs_time_limit=3 * 60 * 60):
        completed_or_fizzled_fws = LPAD.get_fw_ids({"state": {"$in": ["COMPLETED", "FIZZLED"]}})
        # lost_fws = LPAD.detect_lostruns(expiration_secs=lost_runs_time_limit, fizzle=True)[1]
        print(f"Completed or Fizzled fw_ids: {completed_or_fizzled_fws}")
        # print(f"Lost fw_ids: {lost_fws}")
        fws = [LPAD.get_fw_by_id(fw_id) for fw_id in completed_or_fizzled_fws] #+lost_fws]
        for fw in fws:
            if "ssh_info" in fw.spec:
                ssh_info = fw.spec["ssh_info"]
                if "ssh_metrics" in ssh_info:
                    for entry in ssh_info["ssh_metrics"]:
                        port = entry['port']
                        self.to_delete_ports.append(port)
                        self.to_delete_fw_ids.append(fw.fw_id)
                if "ssh_custom_metrics" in ssh_info:
                    for entry in ssh_info["ssh_custom_metrics"]:
                        port = entry['port']['mapped_port']
                        self.to_delete_ports.append(port)
                        self.to_delete_fw_ids.append(fw.fw_id)

            self.to_delete_knodes.extend(fw.spec["jrms_info"]["nodenames"])

        return self.to_delete_ports

    def find_ports_from_fw_id(self, fw_id):
        fw = LPAD.get_fw_by_id(int(fw_id))
        if "ssh_info" in fw.spec:
            ssh_info = fw.spec["ssh_info"]
            if "ssh_metrics" in ssh_info:
                for entry in ssh_info["ssh_metrics"]:
                    port = entry['port']
                    self.to_delete_ports.append(port)
                    self.to_delete_fw_ids.append(fw.fw_id)
            if "ssh_custom_metrics" in ssh_info:
                for entry in ssh_info["ssh_custom_metrics"]:
                    port = entry['port']['mapped_port']
                    self.to_delete_ports.append(port)
                    self.to_delete_fw_ids.append(fw.fw_id)

        self.to_delete_knodes.extend(fw.spec["jrms_info"]["nodenames"])

        return self.to_delete_ports
    
    def delete_ports(self):
        # send the cmd to REST API server listening 8888 to delete the ports
        for port, fw_id in zip(self.to_delete_ports, self.to_delete_fw_ids):
            print(f"Delete port {port} used by fw_id {fw_id}, check the log at {LOG_PATH}delete_ports_logger.log")
            cmd = f"lsof -i:{port}; if [ $? -eq 0 ]; then kill -9 $(lsof -t -i:{port}); fi"
            response = Ssh.send_command(cmd)
            response['cmd'] = cmd
            response['port'] = port
            response['complete_fw_id'] = fw_id
            logger = Logger('delete_ports_logger')
            logger.log(response)

    def delete_nodes(self):
        # send the cmd to REST API server listening 8888 to delete the nodes
        try:
            cmd = f"kubectl delete nodes {' '.join(self.to_delete_knodes)}"
        except Exception as e:
            print(f"Error: {e}")
            return
        
        print(f"Delete nodes {self.to_delete_knodes}, check the log at {LOG_PATH}delete_nodes_logger.log")
        response = Ssh.send_command(cmd)
        response['cmd'] = cmd
        response['nodes'] = self.to_delete_knodes
        logger = Logger('delete_nodes_logger')
        logger.log(response)

class JrmManager:
    def __init__(self):
        self.slurm = Slurm()
        self.jrm = Jrm()
        self.ssh = Ssh()
        self.task = Task(self.slurm, self.jrm, self.ssh)

        self.manage_ports = MangagePorts()

        self.available_kubelet_ports = Ssh.request_available_ports(10000, 19999)["ports"]
        self.available_custom_metrics_ports = Ssh.request_available_ports(20000, 49999)["ports"]

    def launch_jrm_script(self):
        # check and delete the ports used by the completed and lost fireworks on local
        self.manage_ports.find_ports_from_lpad()
        print(f"Found used ports: {self.manage_ports.to_delete_ports}")
        self.manage_ports.delete_ports()
        self.manage_ports.delete_nodes()
        print(f"Delete nodes: {self.manage_ports.to_delete_knodes}")

        # delete wf from LaunchPad
        for fw_id in set(self.manage_ports.to_delete_fw_ids):
            print(f"Delete workflow {fw_id} from Launch Pad")
            LPAD.delete_wf(int(fw_id))

        # time.sleep(3)
        
        # run db, apiserver ssh
        print(f"Connect to db and apiserver via \n ssh_key: {self.ssh.ssh_key}, remote: {self.ssh.remote}, remote_proxy: {self.ssh.remote_proxy}")
        ssh_db = self.ssh.connect_db()
        if "error" in ssh_db:
            print(f"Error in connecting to db. Check the log at {LOG_PATH}connect_db_logger.log")
            return None
        
        ssh_apiserver = self.ssh.connect_apiserver(self.jrm.apiserver_port)
        if "error" in ssh_apiserver:
            print(f"Error in connecting to apiserver. Check the log at {LOG_PATH}connect_apiserver_logger.log")
            return None

        # check if vkubelet_pod_ips is greater than nodes
        if len(self.jrm.vkubelet_pod_ips) < self.slurm.nodes:
            print(f"Waring: vkubelet_pod_ips is less than nodes. vkubelet_pod_ips: {self.jrm.vkubelet_pod_ips}, nodes: {self.slurm.nodes}")
            # extend vkubelet_pod_ips to nodes with the first ip
            self.jrm.vkubelet_pod_ips.extend([self.jrm.vkubelet_pod_ips[0]] * (self.slurm.nodes - len(self.jrm.vkubelet_pod_ips)))
            print(f"Extend vkubelet_pod_ips to {self.jrm.vkubelet_pod_ips}")

        tasks, nodenames = [], []
        for node_index in range(self.slurm.nodes):
            print("====================================")
            unique_id = str(uuid.uuid4())[:8]
            nodename = f"{self.jrm.nodename}-{unique_id}"

            remote_ssh_cmds, kubelet_port = self.task.get_remote_ssh_cmds(nodename, self.available_kubelet_ports, self.available_custom_metrics_ports)
            print(f"Node {nodename} is using ip {self.jrm.vkubelet_pod_ips[node_index]}")
            print(f"SSH commands on the batch job script: {remote_ssh_cmds}")
            script = self.task.get_jrm_script(nodename, kubelet_port, remote_ssh_cmds, self.jrm.vkubelet_pod_ips[node_index])
            tasks.append(ScriptTask.from_str(f"cat << EOF > {nodename}.sh\n{script}\nEOF"))
            tasks.append(ScriptTask.from_str(f"chmod +x {nodename}.sh"))
            nodenames.append(nodename)

        exec_task = ScriptTask.from_str(f"for nodename in {' '.join(nodenames)}; do srun --nodes=1 sh $nodename.sh& done; wait; echo 'All nodes are done'")
        tasks.append(exec_task)

        fw = Firework(tasks, name=f"{self.jrm.site}_{nodename}")

        fw.spec["_category"] = self.jrm.site

        pre_rocket_string = f"conda activate fireworks\nssh -NfL 27017:localhost:27017 {self.ssh.remote}"

        queueadapter = {
            "job_name": f"{self.jrm.site}_{nodename}",
            "walltime": self.slurm.walltime,
            "qos": self.slurm.qos,
            "nodes": self.slurm.nodes,
            "account": self.slurm.account,
            "constraint": self.slurm.constraint,
            "pre_rocket": pre_rocket_string,
        }
        if self.slurm.reservation:
            queueadapter["reservation"] = self.slurm.reservation

        fw.spec["_queueadapter"] = queueadapter

        fw.spec["jrms_info"] = {
            "nodenames": nodenames,
            "jrm_ports": self.task.jrm_ports,
            "apiserver_port": self.jrm.apiserver_port,
            "kubeconfig": self.jrm.kubeconfig,
            "control_plane_ip": self.jrm.control_plane_ip,
            "vkubelet_pod_ips": self.jrm.vkubelet_pod_ips,
            "site": self.jrm.site,
            "image": self.jrm.image,
            "mapped_custom_metrics_ports": {str(k): str(v) for k, v in self.task.dict_mapped_custom_metrics_ports.items()}
        }

        fw.spec["ssh_info"] = {
            "ssh_metrics": self.task.ssh_metrics_cmds,
            "ssh_db": ssh_db,
            "ssh_apiserver": ssh_apiserver,
            "ssh_custom_metrics": self.task.ssh_custom_metrics_cmds
        }

        wf = Workflow([fw], {fw: []})
        wf.name = f"{self.jrm.site}_{nodename}"
        return wf

    def add_jrm(self):
        result = self.launch_jrm_script()
        wf = result if result else None
        if wf is None:
            print("Error: No workflow is created")
            return
        
        LPAD.add_wf(wf)
        print(f"Add workflow {wf.name} to LaunchPad")

    @classmethod
    def delete_jrm(cls, fw_id):
        manage_ports = MangagePorts()
        manage_ports.find_ports_from_fw_id(fw_id)
        manage_ports.delete_ports()
        manage_ports.delete_nodes()
        print(f"Delete nodes: {manage_ports.to_delete_knodes}")
        LPAD.delete_wf(int(fw_id))
        print(f"Delete workflow {fw_id} from LaunchPad")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["add_wf", "delete_wf"], help="Action to perform")
    parser.add_argument("--fw_id", help="Firework ID to delete")

    args = parser.parse_args()


    if args.action == "add_wf":
        jrm_manager = JrmManager()
        jrm_manager.add_jrm()
    elif args.action == "delete_wf":
        if args.fw_id is None:
            print("Please provide a Firework ID to delete")
        else:
            JrmManager.delete_jrm(args.fw_id)