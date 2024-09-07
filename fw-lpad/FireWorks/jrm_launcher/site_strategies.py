from abc import ABC, abstractmethod
import base64

class BaseSiteStrategy(ABC):
    def __init__(self, task_manager):
        self.task_manager = task_manager

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

class PerlmutterStrategy(BaseSiteStrategy):
    def build_ssh_command(self, port, reverse, remote_port=None):
        if reverse:
            remote_port = remote_port or port
            return f"ssh -NfR {port}:localhost:{remote_port} {self.task_manager.ssh.remote}"
        else:
            return f"ssh -NfL {port}:localhost:{port} {self.task_manager.ssh.remote}"

    def build_container_command(self, nodename):
        return f"shifter --image={self.task_manager.jrm.image} -- /bin/bash -c \"cp -r /vk-cmd `pwd`/{nodename}\""

    def get_connection_info(self):
        return f"ssh_key: {self.task_manager.ssh.ssh_key}, remote: {self.task_manager.ssh.remote}, remote_proxy: {self.task_manager.ssh.remote_proxy}"

    def get_exec_task_cmd(self, nodenames):
        srun_command = f"srun --nodes=1 sh $nodename.sh&"
        return f"for nodename in {' '.join(nodenames)}; do {srun_command} done; wait; echo 'All nodes are done'"

    def get_pre_rocket_string(self):
        return f"conda activate fireworks\nssh -NfL 27017:localhost:27017 {self.task_manager.ssh.remote}"

class OrnlStrategy(BaseSiteStrategy):
    def build_ssh_command(self, port, reverse, remote_port=None):
        if reverse:
            remote_port = remote_port or port
            return f"ssh -NfR {port}:localhost:{remote_port} {self.task_manager.ssh.remote}"
        else:
            return f"ssh -NfL {port}:localhost:{port} {self.task_manager.ssh.remote}"

    def build_container_command(self, nodename):
        return f"shifter --image={self.task_manager.jrm.image} -- /bin/bash -c \"cp -r /vk-cmd `pwd`/{nodename}\""

    def get_connection_info(self):
        return f"password: {self.task_manager.ssh.password}, remote: {self.task_manager.ssh.remote}, remote_proxy: {self.task_manager.ssh.remote_proxy}"

    def get_exec_task_cmd(self, nodenames):
        return f"for nodename in {' '.join(nodenames)}; do srun --cpu-bind=none --nodes=1 sh $nodename.sh& done; wait; echo 'All nodes are done'"

    def get_pre_rocket_string(self):
        decoded_password = base64.b64decode(self.task_manager.ssh.password).decode('utf-8')
        return f"""
        conda activate fireworks
        expect -c 'spawn ssh -NfL 27017:localhost:27017 {self.task_manager.ssh.remote}; expect "Password:"; send "{decoded_password}\\r"; expect eof'
        """

class TestStrategy(BaseSiteStrategy):
    def build_ssh_command(self, port, reverse, remote_port=None):
        if reverse:
            remote_port = remote_port or port
            return f"ssh -NfR {port}:localhost:{remote_port} {self.task_manager.ssh.remote}"
        else:
            return f"ssh -NfL {port}:localhost:{port} {self.task_manager.ssh.remote}"

    def build_container_command(self, nodename):
        return f"shifter --image={self.task_manager.jrm.image} -- /bin/bash -c \"cp -r /vk-cmd `pwd`/{nodename}\""

    def get_connection_info(self):
        return f"ssh_key: {self.task_manager.ssh.ssh_key}, remote: {self.task_manager.ssh.remote}, remote_proxy: {self.task_manager.ssh.remote_proxy}"

    def get_exec_task_cmd(self, nodenames):
        srun_command = f"srun --nodes=1 sh $nodename.sh&"
        return f"for nodename in {' '.join(nodenames)}; do {srun_command} done; wait; echo 'All nodes are done'"

    def get_pre_rocket_string(self):
        return f"conda activate fireworks\nssh -NfL 27017:localhost:27017 {self.task_manager.ssh.remote}"

# Add more strategies for new sites here
