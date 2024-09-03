import json
import os
from datetime import datetime
from monty.serialization import loadfn, dumpfn
import subprocess
import time
from queue import Queue

from log import Logger

from concurrent.futures import ThreadPoolExecutor

import socket

class Tool:
    @classmethod
    def send_command(cls, command):
        try:
            # Using shell=True to run the command in the background
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1)  # Give the process a moment to start
            if process.poll() is None:  # Check if the process is still running (background)
                return {"status": "Command completed and sent to background"}
            else:
                stdout, stderr = process.communicate()
                return {"status": "Command failed", "error": stderr.decode('utf-8')}
        except Exception as e:
            return {"status": "Command failed", "error": str(e)}

    @classmethod
    def check_port(cls, port, ip="127.0.0.1"):
        """Check if a specific port is active using netstat."""
        try:
            output = subprocess.check_output(f"netstat -an | grep {port}", shell=True)
            return True if output else False
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def check_port_socket(cls, port, ip="127.0.0.1"):
        """Check if a specific port is available by attempting to bind a socket to it."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((ip, port))
                return True
            except OSError:
                print(f"Port {port} is already in use")
                return False

    @classmethod
    def get_available_ports(cls, start_port, end_port, ip="127.0.0.1", max_workers=50):
        """Generate available ports in the given range that are not currently in use, using socket binding."""
        available_ports = Queue()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(cls.check_port_socket, port, ip): port for port in range(start_port, end_port)}
            for future in futures:
                if future.result():
                    available_ports.put(futures[future])

        return available_ports

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
            print(f"Adding custom metrics port {custom_metrics_port} and mapped port {mapped_port} for nodename {nodename}")
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

    def _create_ssh_command(self, port, reverse_tunnel, nohup=True):
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
        """Ensure the SSH connection is established by checking the port using netstat."""
        max_retries = 8
        for attempt in range(max_retries):
            response = Tool.send_command(cmd)
            if response.get("status") == "Command completed and sent to background" and Tool.check_port(port):
                self._log_response(response, logger_name, cmd, port, nodename)
                return response
            print(f"Retrying SSH connection for port {port} (attempt {attempt + 1}/{max_retries})")
            time.sleep(2)  # Add a delay before retrying
        response = {"error": f"Failed to establish connection on port {port} after {max_retries} attempts"}
        self._log_response(response, logger_name, cmd, port, nodename)
        return response

    def connect_db(self):
        cmd = self._create_ssh_command(27017, reverse_tunnel=True)
        response = self._ensure_connection(cmd, 27017, 'connect_db_logger', "DB Connection")
        if response.get("status") == "Command completed and sent to background":
            self.port_nodename_table.add_record(27017, "DB Connection")
        return response

    def connect_apiserver(self, apiserver_port):
        cmd = self._create_ssh_command(apiserver_port, reverse_tunnel=True)
        response = self._ensure_connection(cmd, apiserver_port, 'connect_apiserver_logger', "API Server")
        if response.get("status") == "Command completed and sent to background":
            self.port_nodename_table.add_record(apiserver_port, "API Server")
        return response

    def connect_metrics_server(self, kubelet_port, nodename):
        cmd = self._create_ssh_command(kubelet_port, reverse_tunnel=False)
        response = self._ensure_connection(cmd, kubelet_port, 'connect_metrics_server_logger', nodename)
        if response.get("status") == "Command completed and sent to background":
            self.port_nodename_table.add_record(kubelet_port, nodename)
        return response

    def connect_custom_metrics(self, mapped_port, custom_metrics_port, nodename):
        cmd = self._create_ssh_command(mapped_port, reverse_tunnel=False)
        response = self._ensure_connection(cmd, mapped_port, 'connect_custom_metrics_logger', nodename)
        if response.get("status") == "Command completed and sent to background":
            self.port_nodename_table.add_record(mapped_port, nodename, mapped_port, custom_metrics_port)
            self._log_response(response, 'connect_custom_metrics_logger', cmd, {"mapped_port": str(mapped_port), "custom_metrics_port": str(custom_metrics_port)}, nodename)
        return response


class PerlmutterSsh(BaseSsh):
    def _create_ssh_command(self, port, reverse_tunnel, nohup=True):
        if not self.ssh_key or not self.remote_proxy or not self.remote:
            raise ValueError("Missing SSH parameters for Perlmutter site.")

        if reverse_tunnel:
            cmd = (
                f"ssh -o StrictHostKeyChecking=no "
                f"-i {self.ssh_key} "
                f"-o ProxyCommand='ssh -o StrictHostKeyChecking=no -i {self.ssh_key} -W %h:%p {self.remote_proxy}' "
                f"-NfR {port}:localhost:{port} {self.remote}"
            )
        else:
            cmd = (
                f"ssh -o StrictHostKeyChecking=no "
                f"-i {self.ssh_key} "
                f"-o ProxyCommand='ssh -o StrictHostKeyChecking=no -i {self.ssh_key} -W %h:%p {self.remote_proxy}' "
                f"-NfL *:{port}:localhost:{port} {self.remote}"
            )

        return cmd


class OrnlSsh(BaseSsh):
    def _create_ssh_command(self, port, reverse_tunnel, nohup=True):
        if not self.build_ssh_script or not self.password:
            raise ValueError("Missing SSH parameters for ORNL site.")

        orig_cmd = f"{self.build_ssh_script} {port} {str(reverse_tunnel).lower()} {self.password}"
        if nohup:
            cmd = f"nohup {orig_cmd} > /dev/null 2>&1"
        else:
            cmd = orig_cmd
        return cmd
    

class SshManager:
    def __init__(self, site_name, config_file):
        self.ssh_instance = self.get_ssh_instance(site_name, config_file)

    def get_ssh_instance(self, site_name, config_file):
        if site_name == "perlmutter":
            return PerlmutterSsh(config_file)
        elif site_name == "ornl":
            return OrnlSsh(config_file)
        else:
            raise ValueError(f"Site {site_name} is not supported.")

    def __getattr__(self, name):
        """
        Dynamically delegate method calls to the underlying ssh_instance.
        """
        return getattr(self.ssh_instance, name)
