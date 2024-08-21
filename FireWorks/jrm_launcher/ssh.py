from monty.serialization import loadfn
import requests, json

from log import Logger

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

    def connect_db(self):
        cmd = self._create_ssh_command(27017, reverse_tunnel=True)
        response = Tool.send_command(cmd)
        self._log_response(response, 'connect_db_logger', cmd, 27017)
        return response

    def connect_apiserver(self, apiserver_port):
        cmd = self._create_ssh_command(apiserver_port, reverse_tunnel=True)
        response = Tool.send_command(cmd)
        self._log_response(response, 'connect_apiserver_logger', cmd, apiserver_port)
        return response

    def connect_metrics_server(self, kubelet_port, nodename):
        cmd = self._create_ssh_command(kubelet_port, reverse_tunnel=False)
        response = Tool.send_command(cmd)
        self._log_response(response, 'connect_metrics_server_logger', cmd, kubelet_port, nodename)
        return response

    def connect_custom_metrics(self, mapped_port, custom_metrics_port, nodename):
        cmd = self._create_ssh_command(mapped_port, reverse_tunnel=False)
        response = Tool.send_command(cmd)
        self._log_response(response, 'connect_custom_metrics_logger', cmd, {"mapped_port": str(mapped_port), "custom_metrics_port": str(custom_metrics_port)}, nodename)
        return response


class PerlmutterSsh(BaseSsh):
    def _create_ssh_command(self, port, reverse_tunnel, nohup=True):
        if not self.ssh_key or not self.remote_proxy or not self.remote:
            raise ValueError("Missing SSH parameters for Perlmutter site.")

        if reverse_tunnel:
            cmd = f"ssh -i {self.ssh_key} -J {self.remote_proxy} -NfR {port}:localhost:{port} {self.remote}"
        else:
            cmd = f"ssh -i {self.ssh_key} -J {self.remote_proxy} -NfL *:{port}:localhost:{port} {self.remote}"

        # Check if the command is already running and if not, run it
        return cmd


class OrnlSsh(BaseSsh):
    def _create_ssh_command(self, port, reverse_tunnel, nohup=True):
        if not self.build_ssh_script or not self.password:
            raise ValueError("Missing SSH parameters for ORNL site.")

        orig_cmd = f"{self.build_ssh_script} {port} {str(reverse_tunnel).lower()} {self.password}"
        if nohup:
            cmd = f"nohup {orig_cmd} > /dev/null 2>&1 &"
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

# Example usage:
# ssh_manager = SshManager(site_name="perlmutter", config_file="path/to/config.yaml")
# ssh_manager.connect_db()
