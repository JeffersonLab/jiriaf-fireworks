import argparse
from log import Logger
from __init__ import LOG_PATH, LPAD
import jrm, slurm, ssh, launch, manage_port
from site_config import get_site_config
import inspect

class MainJrmManager:
    def __init__(self, config_file):
        self.slurm = slurm.ReadConfig(config_file)
        self.jrm = jrm.ReadConfig(config_file)
        self.ssh = ssh.SshManager(self.jrm.site, config_file)
        self.jrm_manager = launch.JrmManager(self.slurm, self.jrm, self.ssh)
        self.config_file = config_file
        self.site_config = get_site_config(self.jrm.config_class if self.jrm.config_class else self.jrm.site)

    def add_jrm(self):
        result = self.jrm_manager.launch_jrm_script()
        wf = result if result else None
        if wf is None:
            print("Error: No workflow is created")
            return
        
        LPAD.add_wf(wf)
        print(f"Add workflow {wf.name} to LaunchPad")

    @classmethod
    def delete_jrm(cls, fw_id):
        manage_ports = manage_port.MangagePorts()
        manage_ports.find_ports_from_fw_id(fw_id)
        manage_ports.delete_ports()
        manage_ports.delete_nodes()
        print(f"Delete nodes: {manage_ports.to_delete_knodes}")
        LPAD.delete_wf(int(fw_id))
        print(f"Delete workflow {fw_id} from LaunchPad")

    @classmethod
    def delete_ports(cls, start, end):
        command = f"for port in $(seq {start} {end}); do pid=$(lsof -t -i:$port); if [ -n \"$pid\" ]; then echo \"Killing process on port $port with PID $pid\"; kill -9 $pid; else echo \"No process running on port $port\"; fi; done"
        print(f"Delete ports from {start} to {end}, check the log at {LOG_PATH}delete_ports_logger.log")
        response = ssh.Tool.send_command(command)
        logger = Logger('delete_ports_logger')
        logger.log(response)

    def connect(self, connect_type, port=None, nodename=None, mapped_port=None, custom_metrics_port=None):
        if connect_type == "db":
            self.ssh.connect_db()
        elif connect_type == "apiserver":
            if port is None:
                raise ValueError("Port number is required for connecting to the apiserver.")
            self.ssh.connect_apiserver(port)
        elif connect_type == "metrics":
            if port is None or nodename is None:
                raise ValueError("Port number and nodename are required for connecting to the metrics server.")
            self.ssh.connect_metrics_server(port, nodename)
        elif connect_type == "custom_metrics":
            if mapped_port is None or custom_metrics_port is None or nodename is None:
                raise ValueError("Mapped port, custom metrics port, and nodename are required for connecting custom metrics.")
            self.ssh.connect_custom_metrics(mapped_port, custom_metrics_port, nodename)
        else:
            raise ValueError("Invalid connect type specified.")
        
        # Save the port-nodename table after any connection
        self.ssh.ssh_instance.port_nodename_table.save_table()

    def print_site_config(self):
        print("Site Configuration:")
        print("===================")
        
        print("\nSLURM Configuration:")
        print(f"  Nodes: {self.slurm.nodes}")
        print(f"  Constraint: {self.slurm.constraint}")
        print(f"  Walltime: {self.slurm.walltime}")
        print(f"  QoS: {self.slurm.qos}")
        print(f"  Account: {self.slurm.account}")
        if hasattr(self.slurm, 'reservation') and self.slurm.reservation:
            print(f"  Reservation: {self.slurm.reservation}")
        
        print("\nJRM Configuration:")
        print(f"  Nodename: {self.jrm.nodename}")
        print(f"  Site: {self.jrm.site}")
        print(f"  Control Plane IP: {self.jrm.control_plane_ip}")
        print(f"  API Server Port: {self.jrm.apiserver_port}")
        print(f"  Kubeconfig: {self.jrm.kubeconfig}")
        print(f"  Image: {self.jrm.image}")
        print(f"  VKubelet Pod IPs: {', '.join(self.jrm.vkubelet_pod_ips)}")
        if hasattr(self.jrm, 'custom_metrics_ports') and self.jrm.custom_metrics_ports:
            print(f"  Custom Metrics Ports: {', '.join(map(str, self.jrm.custom_metrics_ports))}")
        print(f"  Config Class: {self.jrm.config_class or 'Not specified'}")
        
        print("\nSSH Configuration:")
        print(f"  Remote Proxy: {self.ssh.remote_proxy}")
        print(f"  Remote: {self.ssh.remote}")
        print(f"  SSH Key: {self.ssh.ssh_key}")
        if self.ssh.build_ssh_script:
            print(f"  Build SSH Script: {self.ssh.build_ssh_script}")
        if self.ssh.password:
            print("  Password: [REDACTED]")
        
        print(f"\nConfiguration File: {self.config_file}")

        print("\nBaseSiteConfig Implementation:")
        print(f"  Class: {self.site_config.__class__.__name__}")
        print("  Methods:")
        for method_name in [
            'setup_remote_ssh_cmd',
            'build_container_command',
            'get_connection_info',
            'get_exec_task_cmd',
            'get_pre_rocket_string',
            'setup_local_ssh_cmd',
            'get_sleep_time'
        ]:
            method = getattr(self.site_config, method_name)
            print(f"    - {method_name}:")
            print(f"      {inspect.getsource(method).strip()}")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["add_wf", "delete_wf", "delete_ports", "connect", "print_config"], help="Action to perform")
    parser.add_argument("--fw_id", help="Firework ID to delete")
    parser.add_argument("--start", type=int, help="Start port to delete")
    parser.add_argument("--end", type=int, help="End port to delete")
    parser.add_argument("--site_config_file", type=str, help="Path to the site-specific configuration file.")
    parser.add_argument("--connect_type", choices=["db", "apiserver", "metrics", "custom_metrics"], help="Type of connection to establish.")
    parser.add_argument("--port", type=int, help="Port number for apiserver or metrics connection.")
    parser.add_argument("--nodename", type=str, help="Nodename for metrics or custom metrics connection.")
    parser.add_argument("--mapped_port", type=int, help="Mapped port for custom metrics connection.")
    parser.add_argument("--custom_metrics_port", type=int, help="Custom metrics port for custom metrics connection.")
    parser.add_argument("--print_config", action="store_true", help="Print the site configuration")

    args = parser.parse_args()

    if args.action == "add_wf":        
        jrm_manager = MainJrmManager(args.site_config_file)
        jrm_manager.add_jrm()
    elif args.action == "delete_wf":
        if args.fw_id is None:
            print("Please provide a Firework ID to delete")
        else:
            MainJrmManager.delete_jrm(args.fw_id)
    elif args.action == "delete_ports":
        if args.start is None or args.end is None:
            print("Please provide start and end ports to delete")
        else:
            MainJrmManager.delete_ports(args.start, args.end)
    elif args.action == "connect":
        if args.connect_type is None:
            print("Please specify a connect type.")
        else:
            jrm_manager = MainJrmManager(args.site_config_file)
            jrm_manager.connect(args.connect_type, port=args.port, nodename=args.nodename, mapped_port=args.mapped_port, custom_metrics_port=args.custom_metrics_port)

    elif args.action == "print_config":
        if args.site_config_file is None:
            print("Please provide a site configuration file using --site_config_file")
        else:
            jrm_manager = MainJrmManager(args.site_config_file)
            jrm_manager.print_site_config()
