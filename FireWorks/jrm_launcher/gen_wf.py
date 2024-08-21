import argparse
from log import Logger
from __init__ import LOG_PATH, LPAD
import jrm, slurm, ssh, launch, manage_port

class MainJrmManager:
    def __init__(self, config_file):
        self.slurm = slurm.ReadConfig(config_file)
        self.jrm = jrm.ReadConfig(config_file)
        self.ssh = ssh.SshManager(self.jrm.site, config_file)
        self.jrm_manager = self.get_jrm_manager()

    def get_jrm_manager(self):
        if self.jrm.site == "perlmutter":
            return launch.PerlmutterJrmManager(self.slurm, self.jrm, self.ssh)
        elif self.jrm.site == "ornl":
            return launch.OrnlJrmManager(self.slurm, self.jrm, self.ssh)
        else:
            raise ValueError(f"Site {self.site_name} is not supported.")

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["add_wf", "delete_wf", "delete_ports"], help="Action to perform")
    parser.add_argument("--fw_id", help="Firework ID to delete")
    parser.add_argument("--start", type=int, help="Start port to delete")
    parser.add_argument("--end", type=int, help="End port to delete")
    parser.add_argument("--site_config_file", type=str, help="Path to the site-specific configuration file.")

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