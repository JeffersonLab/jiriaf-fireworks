from monty.serialization import loadfn

class ReadConfig:
    def __init__(self, config_file):
        self.node_config = loadfn(config_file) if config_file else {}
        if not self.node_config:
            raise ValueError("node-config.yaml is empty")
        self.nodes = self.node_config["slurm"]["nodes"]
        self.qos = self.node_config["slurm"]["qos"]
        self.walltime = self.node_config["slurm"]["walltime"]
        self.account = self.node_config["slurm"]["account"]
        self.constraint = self.node_config["slurm"]["constraint"]
        self.reservation = self.node_config["slurm"]["reservation"] if "reservation" in self.node_config["slurm"] else None