from abc import ABC, abstractmethod
import base64

class BaseSiteConfig(ABC):
    @abstractmethod
    def build_ssh_command(self, port, reverse, remote_port=None):
        pass

    @abstractmethod
    def build_container_command(self, nodename):
        pass

    @abstractmethod
    def get_connection_info(self):
        pass

    @abstractmethod
    def get_exec_task_cmd(self, nodenames):
        pass

    @abstractmethod
    def get_pre_rocket_string(self):
        pass

    @abstractmethod
    def create_ssh_command(self, port, reverse_tunnel, nohup=True):
        pass

    @abstractmethod
    def get_sleep_time(self):
        pass

    def set_managers(self, task_manager, ssh_manager):
        self.task_manager = task_manager
        self.ssh_manager = ssh_manager

class PerlmutterConfig(BaseSiteConfig):
    def build_ssh_command(self, port, reverse, remote_port=None):
        if reverse:
            remote_port = remote_port or port
            return f"ssh -NfR {port}:localhost:{remote_port} {self.ssh_manager.remote}"
        else:
            return f"ssh -NfL {port}:localhost:{port} {self.ssh_manager.remote}"

    def build_container_command(self, nodename):
        return f"shifter --image={self.task_manager.jrm.image} -- /bin/bash -c \"cp -r /vk-cmd `pwd`/{nodename}\""

    def get_connection_info(self):
        return f"ssh_key: {self.ssh_manager.ssh_key}, remote: {self.ssh_manager.remote}, remote_proxy: {self.ssh_manager.remote_proxy}"

    def get_exec_task_cmd(self, nodenames):
        srun_command = f"srun --nodes=1 sh $nodename.sh&"
        return f"for nodename in {' '.join(nodenames)}; do {srun_command} done; wait; echo 'All nodes are done'"

    def get_pre_rocket_string(self):
        return f"conda activate fireworks\nssh -NfL 27017:localhost:27017 {self.ssh_manager.remote}"

    def create_ssh_command(self, port, reverse_tunnel, nohup=True):
        if reverse_tunnel:
            cmd = (
                f"ssh -o StrictHostKeyChecking=no "
                f"-i {self.ssh_manager.ssh_key} "
                f"-o ProxyCommand='ssh -o StrictHostKeyChecking=no -i {self.ssh_manager.ssh_key} -W %h:%p {self.ssh_manager.remote_proxy}' "
                f"-NfR {port}:localhost:{port} {self.ssh_manager.remote}"
            )
        else:
            cmd = (
                f"ssh -o StrictHostKeyChecking=no "
                f"-i {self.ssh_manager.ssh_key} "
                f"-o ProxyCommand='ssh -o StrictHostKeyChecking=no -i {self.ssh_manager.ssh_key} -W %h:%p {self.ssh_manager.remote_proxy}' "
                f"-NfL *:{port}:localhost:{port} {self.ssh_manager.remote}"
            )
        return cmd

    def get_sleep_time(self):
        return 3

class OrnlConfig(BaseSiteConfig):
    def build_ssh_command(self, port, reverse, remote_port=None):
        decoded_password = base64.b64decode(self.task_manager.ssh.password).decode('utf-8')
        if reverse:
            remote_port = remote_port or port  # Use remote_port if provided, otherwise fall back to port
            return f"expect -c 'spawn ssh -NfR {port}:localhost:{remote_port} {self.task_manager.ssh.remote}; expect \"Password:\"; send \"{decoded_password}\\r\"; expect eof'"
        else:
            return f"expect -c 'spawn ssh -NfL {port}:localhost:{port} {self.task_manager.ssh.remote}; expect \"Password:\"; send \"{decoded_password}\\r\"; expect eof'"

    def build_container_command(self, nodename):
        return f"apptainer exec $HOME/vk-cmd_main.sif cp -r /vk-cmd `pwd`/{nodename}"

    def get_connection_info(self):
        return f"password: {self.ssh_manager.password}, remote: {self.ssh_manager.remote}, remote_proxy: {self.ssh_manager.remote_proxy}"

    def get_exec_task_cmd(self, nodenames):
        return f"for nodename in {' '.join(nodenames)}; do srun --cpu-bind=none --nodes=1 sh $nodename.sh& done; wait; echo 'All nodes are done'"

    def get_pre_rocket_string(self):
        decoded_password = base64.b64decode(self.ssh_manager.password).decode('utf-8')
        return f"""
        conda activate fireworks
        expect -c 'spawn ssh -NfL 27017:localhost:27017 {self.ssh_manager.remote}; expect "Password:"; send "{decoded_password}\\r"; expect eof'
        """

    def create_ssh_command(self, port, reverse_tunnel, nohup=True):
        if not self.ssh_manager.build_ssh_script or not self.ssh_manager.password:
            raise ValueError("Missing SSH parameters for ORNL site.")

        orig_cmd = f"{self.ssh_manager.build_ssh_script} {port} {str(reverse_tunnel).lower()} {self.ssh_manager.password}"
        if nohup:
            cmd = f"nohup {orig_cmd} > /dev/null 2>&1 &"
        else:
            cmd = orig_cmd
        return cmd

    def get_sleep_time(self):
        return 3

class TestConfig(BaseSiteConfig):
    def build_ssh_command(self, port, reverse, remote_port=None):
        if reverse:
            remote_port = remote_port or port
            return f"ssh -NfR {port}:localhost:{remote_port} {self.ssh_manager.remote}"
        else:
            return f"ssh -NfL {port}:localhost:{port} {self.ssh_manager.remote}"

    def build_container_command(self, nodename):
        return f"shifter --image={self.task_manager.jrm.image} -- /bin/bash -c \"cp -r /vk-cmd `pwd`/{nodename}\""

    def get_connection_info(self):
        return f"ssh_key: {self.ssh_manager.ssh_key}, remote: {self.ssh_manager.remote}, remote_proxy: {self.ssh_manager.remote_proxy}"

    def get_exec_task_cmd(self, nodenames):
        srun_command = f"sh $nodename.sh&"
        return f"for nodename in {' '.join(nodenames)}; do {srun_command} done; wait; echo 'All nodes are done'"

    def get_pre_rocket_string(self):
        return f"ssh -NfL 27017:localhost:27017 {self.ssh_manager.remote}"

    def create_ssh_command(self, port, reverse_tunnel, nohup=True):
        if reverse_tunnel:
            cmd = (
                f"ssh -o StrictHostKeyChecking=no "
                f"-i {self.ssh_manager.ssh_key} "
                f"-o ProxyCommand='ssh -o StrictHostKeyChecking=no -i {self.ssh_manager.ssh_key} -W %h:%p {self.ssh_manager.remote_proxy}' "
                f"-NfR {port}:localhost:{port} {self.ssh_manager.remote}"
            )
        else:
            cmd = (
                f"ssh -o StrictHostKeyChecking=no "
                f"-i {self.ssh_manager.ssh_key} "
                f"-o ProxyCommand='ssh -o StrictHostKeyChecking=no -i {self.ssh_manager.ssh_key} -W %h:%p {self.ssh_manager.remote_proxy}' "
                f"-NfL *:{port}:localhost:{port} {self.ssh_manager.remote}"
            )
        return cmd

    def get_sleep_time(self):
        return 3

SITE_CONFIGS = {
    "perlmutter": PerlmutterConfig,
    "ornl": OrnlConfig,
    "test": TestConfig,
}

def get_site_config(config_class):
    config_class = SITE_CONFIGS.get(config_class)
    if config_class is None:
        raise ValueError(f"Unsupported configuration class: {config_class}")
    return config_class()
