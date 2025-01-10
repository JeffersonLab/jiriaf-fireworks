import json
import os
from datetime import datetime
from monty.serialization import loadfn, dumpfn
import requests
import time

from log import Logger
from site_config import get_site_config

class Tool:
    @classmethod
    def send_command(cls, command):
        url = "http://172.17.0.1:8888/run"
        data = {'command': command}
        response = requests.post(url, data=data)
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

    @classmethod
    def check_port(cls, port, ip="127.0.0.1"):
        """Check if a specific port is active by checking for 'No available ports found' in the API response."""
        url = f"http://172.17.0.1:8888/get_ports/{ip}/{port}/{port}"
        response = requests.get(url)
        if response.status_code == 200:
            return "No available ports found" in response.text
        return False

class PortNodenameTable:
    def __init__(self, filepath='/fw/port_table.yaml'):
        self.filepath = filepath
        self.records = self._load_existing_records()

    def _load_existing_records(self):
        if os.path.exists(self.filepath):
            existing_records = loadfn(self.filepath)
            return existing_records if existing_records is not None else []
        return []

    def add_record(self, port, nodename, mapped_port=None, custom_metrics_port=None):
        timestamp = datetime.now().strftime('%Y-%m-%d')
        record = {"port": port, "nodename": nodename, "timestamp": timestamp}
        if mapped_port and custom_metrics_port:
            record["mapped_port"] = mapped_port
            record["custom_metrics_port"] = custom_metrics_port
        self.records.append(record)

    def save_table(self):
        dumpfn(self.records, self.filepath)
        print(f"Port-Nodename table updated at {self.filepath}")

class BaseSsh:
    def __init__(self, config_file):
        self.node_config = loadfn(config_file) if config_file else {}
        if not self.node_config:
            raise ValueError("node-config.yaml is empty")

        self.remote = self.node_config["ssh"].get("remote")
        self.remote_proxy = self.node_config["ssh"].get("remote_proxy")
        self.ssh_key = self.node_config["ssh"].get("ssh_key")
        self.build_ssh_script = self.node_config["ssh"].get("build_script")
        self.password = self.node_config["ssh"].get("password")

        self.port_nodename_table = PortNodenameTable()

    def _setup_local_ssh_cmd(self, port, reverse_tunnel, nohup=True):
        raise NotImplementedError("Subclasses should implement this method.")

    def _log_response(self, response, logger_name, cmd, port, nodename=None):
        logger = Logger(logger_name)
        response.update({
            "cmd": cmd,
            "remote_proxy": self.remote_proxy,
            "remote": self.remote,
        })
        if nodename:
            response["nodename"] = nodename

        if isinstance(port, dict):
            response["port"] = port
        else:
            response["port"] = str(port)

        logger.log(response)

    def _ensure_connection(self, cmd, port, logger_name, nodename=None):
        """Ensure the SSH connection is established by checking the port using the API."""
        max_retries = 8
        for attempt in range(max_retries):
            response = Tool.send_command(cmd)
            if response.get("status") == "Command completed" and Tool.check_port(port):
                self._log_response(response, logger_name, cmd, port, nodename)
                return response
            print(f"Retrying SSH connection for port {port} (attempt {attempt + 1}/{max_retries})")
            time.sleep(2)  # Add a delay before retrying
        response = {"error": f"Failed to establish connection on port {port} after {max_retries} attempts"}
        self._log_response(response, logger_name, cmd, port, nodename)
        raise ConnectionError(f"Failed to establish connection on port {port} after {max_retries} attempts")

    def connect_db(self):
        try:
            cmd = self._setup_local_ssh_cmd(27017, reverse_tunnel=True)
            response = self._ensure_connection(cmd, 27017, 'connect_db_logger', "DB Connection")
            if response.get("status") == "Command completed":
                self.port_nodename_table.add_record(27017, "DB Connection")
            return response
        except ConnectionError as e:
            print(f"Error: {str(e)}")
            return {"error": str(e)}

    def connect_apiserver(self, apiserver_port):
        try:
            cmd = self._setup_local_ssh_cmd(apiserver_port, reverse_tunnel=True)
            response = self._ensure_connection(cmd, apiserver_port, 'connect_apiserver_logger', "API Server")
            if response.get("status") == "Command completed":
                self.port_nodename_table.add_record(apiserver_port, "API Server")
            return response
        except ConnectionError as e:
            print(f"Error: {str(e)}")
            return {"error": str(e)}

    def connect_metrics_server(self, kubelet_port, nodename):
        try:
            cmd = self._setup_local_ssh_cmd(kubelet_port, reverse_tunnel=False)
            response = self._ensure_connection(cmd, kubelet_port, 'connect_metrics_server_logger', nodename)
            if response.get("status") == "Command completed":
                self.port_nodename_table.add_record(kubelet_port, nodename)
            return response
        except ConnectionError as e:
            print(f"Error: {str(e)}")
            return {"error": str(e)}

    def connect_custom_metrics(self, mapped_port, custom_metrics_port, nodename):
        try:
            if "x" in str(custom_metrics_port):
                remote_port = custom_metrics_port.replace("x", "")
                print(f"x found in custom_metrics_port, remote_port: {remote_port}")
            else:
                remote_port = None
                print(f"x not found in custom_metrics_port, remote_port set as mapped_port: {mapped_port}")
            cmd = self._setup_local_ssh_cmd(mapped_port, reverse_tunnel=False, remote_port=remote_port)
            response = self._ensure_connection(cmd, mapped_port, 'connect_custom_metrics_logger', nodename)
            if response.get("status") == "Command completed":
                self.port_nodename_table.add_record(mapped_port, nodename, mapped_port, custom_metrics_port)
                self._log_response(response, 'connect_custom_metrics_logger', cmd, {"mapped_port": str(mapped_port), "custom_metrics_port": str(custom_metrics_port)}, nodename)
            return response
        except ConnectionError as e:
            print(f"Error: {str(e)}")
            return {"error": str(e)}


class SshManager(BaseSsh):
    def __init__(self, site_name, config_file):
        super().__init__(config_file)
        self.site_config = get_site_config(self.node_config["jrm"].get("config_class") if self.node_config["jrm"].get("config_class") else site_name)
        self.site_config.set_managers(self, self)

    def _setup_local_ssh_cmd(self, port, reverse_tunnel, nohup=True, remote_port=None):
        return self.site_config.setup_local_ssh_cmd(port, reverse_tunnel, remote_port, nohup)

    def get_connection_info(self):
        return self.site_config.get_connection_info()

    def get_exec_task_cmd(self, nodenames):
        return self.site_config.get_exec_task_cmd(nodenames)

    def get_pre_rocket_string(self):
        return self.site_config.get_pre_rocket_string()

    def get_sleep_time(self):
        return self.site_config.get_sleep_time()
