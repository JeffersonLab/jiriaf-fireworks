import sys
import os
import yaml

def load_port_table(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def main():
    if len(sys.argv) < 2:
        print("Usage: python get_node_ports.py <node_name> [<port_table_path>]")
        sys.exit(1)
    node_name = sys.argv[1]
    if len(sys.argv) > 2:
        port_table_path = sys.argv[2]
    else:
        # Default to /fw/port_table.yaml, then try current directory, then parent
        if os.path.exists('/fw/port_table.yaml'):
            port_table_path = '/fw/port_table.yaml'
        elif os.path.exists('port_table.yaml'):
            port_table_path = 'port_table.yaml'
        elif os.path.exists('../port_table.yaml'):
            port_table_path = '../port_table.yaml'
        else:
            print("port_table.yaml not found. Please specify the path as the second argument.")
            sys.exit(1)

    port_table = load_port_table(port_table_path)
    # port_table is a list of dicts
    matches = [entry for entry in port_table if entry.get('nodename') == node_name]
    if not matches:
        print(f"No records found for node '{node_name}' in {port_table_path}.")
        sys.exit(0)
    print(f"Records for node '{node_name}':")
    for entry in matches:
        for k, v in entry.items():
            print(f"  {k}: {v}")
        print("-")

if __name__ == "__main__":
    main() 