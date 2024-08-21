from monty.serialization import loadfn
from components import CONFIG_PATH


class ReadConfig:
    def __init__(self, config_file=CONFIG_PATH):
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
