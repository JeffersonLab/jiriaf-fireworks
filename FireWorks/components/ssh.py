from monty.serialization import loadfn
import requests, json

from components.log import Logger

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
    def __init__(self, config_file, site_config=None):
        self.node_config = loadfn(config_file) if config_file else {}
        if not self.node_config:
            raise ValueError("node-config.yaml is empty")

        self.site_config = site_config or {}
        self.remote = self.node_config["ssh"].get("remote")
        self.remote_proxy = self.node_config["ssh"].get("remote_proxy")
        self.ssh_key = self.node_config["ssh"].get("ssh_key")
        self.build_ssh_script = self.node_config["ssh"].get("build_script")
        self.password = self.node_config["ssh"].get("password")

        # Site-specific command builder
        self.command_builder = self.site_config.get("command_builder", self.default_command_builder)

    def default_command_builder(self, port, reverse_tunnel, nohup):
        """
        Default command builder for SSH key-based authentication.
        """
        if not self.ssh_key or not self.remote or not self.remote_proxy:
            raise ValueError("Missing SSH configuration parameters for default command builder.")

        if reverse_tunnel:
            cmd = f"ssh -i {self.ssh_key} -J {self.remote_proxy} -NfR {port}:localhost:{port} {self.remote}"
        else:
            cmd = f"ssh -i {self.ssh_key} -J {self.remote_proxy} -NfL *:{port}:localhost:{port} {self.remote}"
        return cmd

    def _create_ssh_command(self, port, reverse_tunnel, nohup=True):
        """
        This method uses the command_builder to create SSH commands, 
        allowing site-specific customization.
        """
        return self.command_builder(port, reverse_tunnel, nohup)

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


class SshManager:
    def __init__(self, site_name, config_file):
        site_configs = {
            "perlmutter": {
                "command_builder": self.perlmutter_command_builder
            },
            "ornl": {
                "command_builder": self.ornl_command_builder
            },
            # Add additional sites here as needed
        }

        if site_name not in site_configs:
            raise ValueError(f"Site {site_name} is not supported. Please configure it in the site_configs.")

        site_config = site_configs[site_name]
        self.base_ssh = BaseSsh(config_file=config_file, site_config=site_config)

    def perlmutter_command_builder(self, port, reverse_tunnel, nohup):
        """
        Custom command builder for the Perlmutter site.
        """
        ssh_key = self.base_ssh.ssh_key
        remote_proxy = self.base_ssh.remote_proxy
        remote = self.base_ssh.remote

        if not ssh_key or not remote_proxy or not remote:
            raise ValueError("Missing SSH parameters for Perlmutter site.")

        if reverse_tunnel:
            return f"ssh -i {ssh_key} -J {remote_proxy} -NfR {port}:localhost:{port} {remote}"
        else:
            return f"ssh -i {ssh_key} -J {remote_proxy} -NfL *:{port}:localhost:{port} {remote}"

    def ornl_command_builder(self, port, reverse_tunnel, nohup):
        """
        Custom command builder for the ORNL site with password-based authentication.
        """
        build_ssh_script = self.base_ssh.build_ssh_script
        password = self.base_ssh.password
        print(f"build_ssh_script: {build_ssh_script}, password: {password}")
        if not build_ssh_script or not password:
            raise ValueError("Missing SSH parameters for ORNL site.")

        cmd = f"{build_ssh_script} {port} {str(reverse_tunnel).lower()} {password}"
        if nohup:
            cmd = f"nohup {cmd} > /dev/null 2>&1 &"
        return cmd

    def connect_db(self):
        return self.base_ssh.connect_db()

    def connect_apiserver(self, apiserver_port):
        return self.base_ssh.connect_apiserver(apiserver_port)

    def connect_metrics_server(self, kubelet_port, nodename):
        return self.base_ssh.connect_metrics_server(kubelet_port, nodename)

    def connect_custom_metrics(self, mapped_port, custom_metrics_port, nodename):
        return self.base_ssh.connect_custom_metrics(mapped_port, custom_metrics_port, nodename)

# Example usage:
# ssh_manager = SshManager(site_name="perlmutter")
# ssh_manager.connect_db()
