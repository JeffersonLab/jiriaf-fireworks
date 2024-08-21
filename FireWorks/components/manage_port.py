
from fireworks import Workflow, Firework, LaunchPad, ScriptTask
import time
from monty.serialization import loadfn
import textwrap
import requests, json, logging
import argparse
import concurrent.futures
import uuid


from components.ssh import Tool
from components.log import Logger

from components import LPAD, LOG_PATH

class MangagePorts:
    # inherit from Ssh class
    def __init__(self):
        self.to_delete_ports = []
        self.to_delete_fw_ids = []
        self.to_delete_knodes = []


    def find_ports_from_lpad(self, lost_runs_time_limit=3 * 60 * 60):
        completed_or_fizzled_fws = LPAD.get_fw_ids({"state": {"$in": ["COMPLETED", "FIZZLED"]}})
        # lost_fws = LPAD.detect_lostruns(expiration_secs=lost_runs_time_limit, fizzle=True)[1]
        print(f"Completed or Fizzled fw_ids: {completed_or_fizzled_fws}")
        # print(f"Lost fw_ids: {lost_fws}")
        fws = [LPAD.get_fw_by_id(fw_id) for fw_id in completed_or_fizzled_fws] #+lost_fws]
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
        # send the cmd to REST API server listening 8888 to delete the ports
        for port, fw_id in zip(self.to_delete_ports, self.to_delete_fw_ids):
            print(f"Delete port {port} used by fw_id {fw_id}, check the log at {LOG_PATH}delete_ports_logger.log")
            cmd = f"lsof -i:{port}; if [ $? -eq 0 ]; then kill -9 $(lsof -t -i:{port}); fi"
            response = Tool.send_command(cmd)
            response['cmd'] = cmd
            response['port'] = port
            response['complete_fw_id'] = fw_id
            logger = Logger('delete_ports_logger')
            logger.log(response)

    def delete_nodes(self):
        # send the cmd to REST API server listening 8888 to delete the nodes
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