
from ssh import Tool
from log import Logger
import psutil

from __init__ import LPAD, LOG_PATH

class MangagePorts:
    def __init__(self):
        self.to_delete_ports = []
        self.to_delete_fw_ids = []
        self.to_delete_knodes = []

    def find_ports_from_lpad(self, lost_runs_time_limit=3 * 60 * 60):
        completed_or_fizzled_fws = LPAD.get_fw_ids({"state": {"$in": ["COMPLETED", "FIZZLED"]}})
        print(f"Completed or Fizzled fw_ids: {completed_or_fizzled_fws}")
        fws = [LPAD.get_fw_by_id(fw_id) for fw_id in completed_or_fizzled_fws]
        for fw in fws:
            if "ssh_info" in fw.spec:
                ssh_info = fw.spec["ssh_info"]
                if "ssh_metrics" in ssh_info:
                    for entry in ssh_info["ssh_metrics"]:
                        port = entry['port']
                        self.to_delete_ports.append(port)
                        self.to_delete_fw_ids.append(fw.fw_id)
                if "ssh_custom_metrics" in ssh_info:
                    for entry in ssh_info["ssh_custom_metrics"]:
                        port = entry['port']['mapped_port']
                        self.to_delete_ports.append(port)
                        self.to_delete_fw_ids.append(fw.fw_id)

            self.to_delete_knodes.extend(fw.spec["jrms_info"]["nodenames"])

        return self.to_delete_ports

    def find_ports_from_fw_id(self, fw_id):
        fw = LPAD.get_fw_by_id(int(fw_id))
        if "ssh_info" in fw.spec:
            ssh_info = fw.spec["ssh_info"]
            if "ssh_metrics" in ssh_info:
                for entry in ssh_info["ssh_metrics"]:
                    port = entry['port']
                    self.to_delete_ports.append(port)
                    self.to_delete_fw_ids.append(fw.fw_id)
            if "ssh_custom_metrics" in ssh_info:
                for entry in ssh_info["ssh_custom_metrics"]:
                    port = entry['port']['mapped_port']
                    self.to_delete_ports.append(port)
                    self.to_delete_fw_ids.append(fw.fw_id)

        self.to_delete_knodes.extend(fw.spec["jrms_info"]["nodenames"])

        return self.to_delete_ports
    

    def delete_ports(self):
        # Iterate over the ports and try to kill any process that is using them
        for port, fw_id in zip(self.to_delete_ports, self.to_delete_fw_ids):
            print(f"Attempting to delete port {port} used by fw_id {fw_id}. Check the log at {LOG_PATH}delete_ports_logger.log")
            
            # Ensure the port is an integer
            port = int(port)

            # Check if the port is in use and terminate the process using it
            if not Tool.check_port_socket(port):
                print(f"Deleting process using port {port}")
                response = self.kill_process_using_port(port)
                response['cmd'] = f"Process using port {port} killed"  # Log this as a command
            else:
                response = {"status": "Port not in use", "port": port}
            
            # Log the response
            response['complete_fw_id'] = fw_id
            logger = Logger('delete_ports_logger')
            logger.log(response)

    def kill_process_using_port(self, port):
        """Kill the process using the specified port."""
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.info['connections']:
                    if conn.laddr.port == port:
                        proc.kill()
                        print(f"Process {proc.info['name']} with PID {proc.info['pid']} killed")
                        return {"status": "Process killed", "port": port, "pid": proc.info['pid']}
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return {"status": "No process found", "port": port}



    def delete_nodes(self):
        try:
            cmd = f"kubectl delete nodes {' '.join(self.to_delete_knodes)}"
        except Exception as e:
            print(f"Error: {e}")
            return
        
        print(f"Delete nodes {self.to_delete_knodes}, check the log at {LOG_PATH}delete_nodes_logger.log")
        response = Tool.send_command(cmd)
        response['cmd'] = cmd
        response['nodes'] = self.to_delete_knodes
        logger = Logger('delete_nodes_logger')
        logger.log(response)
