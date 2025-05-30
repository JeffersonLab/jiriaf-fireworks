import uuid
import time
import base64
from fireworks import Workflow, Firework, ScriptTask
from ssh import Tool
from task import TaskManager
from manage_port import MangagePorts
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from site_config import get_site_config

from __init__ import LPAD, LOG_PATH

class BaseJrmManager:
    def __init__(self, slurm_instance, jrm_instance, ssh_instance):
        self.slurm = slurm_instance
        self.jrm = jrm_instance
        self.ssh = ssh_instance
        self.task = TaskManager(self.slurm, self.jrm, self.ssh) 

        self.manage_ports = MangagePorts()

    def launch_jrm_script(self):
        # Clean up ports and nodes
        self.manage_ports.find_ports_from_lpad()
        print(f"Found used ports: {self.manage_ports.to_delete_ports}")
        self.manage_ports.delete_ports()
        self.manage_ports.delete_nodes()
        print(f"Delete nodes: {self.manage_ports.to_delete_knodes}")

        # Delete workflows from LaunchPad
        for fw_id in set(self.manage_ports.to_delete_fw_ids):
            print(f"Delete workflow {fw_id} from Launch Pad")
            LPAD.delete_wf(int(fw_id))

        time.sleep(self.get_sleep_time())

        # Connect to DB and API server
        print(f"Connect to db and apiserver via {self.get_connection_info()}")
        ssh_db = self.ssh.connect_db()
        if "error" in ssh_db:
            print(f"Error in connecting to db. Check the log at {LOG_PATH}connect_db_logger.log")
            print("Stopping workflow creation due to connection failure.")
            return None
        
        ssh_apiserver = self.ssh.connect_apiserver(self.jrm.apiserver_port)
        if "error" in ssh_apiserver:
            print(f"Error in connecting to apiserver. Check the log at {LOG_PATH}connect_apiserver_logger.log")
            print("Stopping workflow creation due to connection failure.")
            return None

        # Ensure vkubelet_pod_ips length matches the number of nodes
        self.ensure_vkubelet_pod_ips()

        # Generate available ports and convert them to queue objects
        available_kubelet_ports = Queue()
        available_custom_metrics_ports = Queue()

        for port in Tool.request_available_ports(10000, 19999)["ports"]:
            available_kubelet_ports.put(port)

        for port in Tool.request_available_ports(20000, 49999)["ports"]:
            available_custom_metrics_ports.put(port)

        tasks, nodenames = [], []
        for node_index in range(self.slurm.nodes):
            print("====================================")
            unique_id = str(uuid.uuid4())[:8]
            nodename = f"{self.jrm.nodename}-{unique_id}"

            remote_ssh_cmds, kubelet_port = self.task.setup_ssh_connections(nodename, available_kubelet_ports, available_custom_metrics_ports)
            if not remote_ssh_cmds:  # If setup_ssh_connections failed
                print(f"Error in setting up SSH connections for node {nodename}")
                print("Stopping workflow creation due to connection failure.")
                return None

            print(f"Node {nodename} is using ip {self.jrm.vkubelet_pod_ips[node_index]}")
            script = self.task.get_jrm_script(nodename, kubelet_port, remote_ssh_cmds, self.jrm.vkubelet_pod_ips[node_index])
            tasks.append(ScriptTask.from_str(f"cat << 'EOF' > {nodename}.sh\n{script}\nEOF"))
            tasks.append(ScriptTask.from_str(f"chmod +x {nodename}.sh"))
            nodenames.append(nodename)
            time.sleep(self.get_sleep_time())

        self.ssh.port_nodename_table.save_table()
        exec_task = ScriptTask.from_str(self.get_exec_task_cmd(nodenames))
        tasks.append(exec_task)

        fw = Firework(tasks, name=f"{self.jrm.site}_{nodenames[0]}")

        fw.spec["_category"] = self.jrm.site

        pre_rocket_string = self.get_pre_rocket_string()

        queueadapter = {
            "job_name": f"{self.jrm.site}_{nodenames[0]}",
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
        wf.name = f"{self.jrm.site}_{nodenames[0]}"
        return wf
    
    def ensure_vkubelet_pod_ips(self):
        if len(self.jrm.vkubelet_pod_ips) < self.slurm.nodes:
            print(f"Waring: vkubelet_pod_ips is less than nodes. vkubelet_pod_ips: {self.jrm.vkubelet_pod_ips}, nodes: {self.slurm.nodes}")
            self.jrm.vkubelet_pod_ips.extend([self.jrm.vkubelet_pod_ips[0]] * (self.slurm.nodes - len(self.jrm.vkubelet_pod_ips)))
            print(f"Extend vkubelet_pod_ips to {self.jrm.vkubelet_pod_ips}")

    def get_sleep_time(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_connection_info(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_exec_task_cmd(self, nodenames):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_pre_rocket_string(self):
        raise NotImplementedError("This method should be implemented by subclasses.")


class JrmManager(BaseJrmManager):
    def __init__(self, slurm_instance, jrm_instance, ssh_instance):
        super().__init__(slurm_instance, jrm_instance, ssh_instance)
        self.site_config = get_site_config(jrm_instance.config_class if jrm_instance.config_class else jrm_instance.site)
        self.site_config.set_managers(self.task, ssh_instance)

    def get_sleep_time(self):
        return self.site_config.get_sleep_time()

    def get_connection_info(self):
        return self.site_config.get_connection_info()

    def get_exec_task_cmd(self, nodenames):
        return self.site_config.get_exec_task_cmd(nodenames)

    def get_pre_rocket_string(self):
        return self.site_config.get_pre_rocket_string()