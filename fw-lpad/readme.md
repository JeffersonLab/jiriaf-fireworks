# JRM Launcher

JRM Launcher is a tool for managing and launching JRM (Job Resource Manager) instances on various computing environments.

## Prerequisites
- MongoDB (for storing workflow of JRM launches)
- Kubernetes API server running
- Valid kubeconfig file for the Kubernetes cluster
- Python 3.9 (for developers)
  - Required Python packages (install via `pip install -r requirements.txt`)

## Adding a Workflow

Follow these steps to add a new workflow:

1. Prepare necessary files and directories:
   - Ensure you have the site configuration file (e.g., `perlmutter_config.yaml`)
   - Create a directory for logs
   - Have a `port_table.yaml` file ready
   - Make sure you have the necessary SSH key (e.g., for NERSC access)

2. Generate or update the site configuration file:
   - Use the template provided in `site_config_template.yaml`
   - Fill in the required fields with your specific site information
   - Example:
     ```yaml
     slurm:
       nodes: 2
       constraint: cpu
       walltime: 00:05:00
       qos: debug
       account: m3792

     jrm:
       nodename: jrm-perlmutter
       site: perlmutter
       control_plane_ip: jiriaf2302
       apiserver_port: 38687
       kubeconfig: /path/to/remote/kubeconfig
       image: docker:jlabtsai/vk-cmd:main
       vkubelet_pod_ips: [172.17.0.1]
       custom_metrics_ports: [2221, 1776, 8088, 2222]
       config_class:

     ssh:
       remote_proxy: user@perlmutter.nersc.gov
       remote: user@128.55.64.13 #this is one of the login nodes in perlmutter
       ssh_key: /root/.ssh/mykey 
       password:
       build_script:
     ```

3. Copy the kubeconfig file to the remote site:
   ```bash
   scp /path/to/local/kubeconfig user@remote:/path/to/remote/kubeconfig
   ```
   Update the `jrm.kubeconfig` in your site config to point to this remote location.

4. Start the JRM Launcher container:
   ```bash
   export logs=/path/to/your/logs/directory
   docker run --name=jrm-fw-lpad -itd --rm --net=host \
     -v ./perlmutter_config.yaml:/fw/perlmutter_config.yaml \
     -v $logs:/fw/logs \
     -v `pwd`/port_table.yaml:/fw/port_table.yaml \
     -v $HOME/.ssh/nersc:/root/.ssh/nersc \
     jlabtsai/jrm-fw-lpad:main
   ```

5. Verify the container is running:
   ```bash
   docker ps
   ```

6. Log into the container:
   ```bash
   docker exec -it jrm-fw-lpad /bin/bash
   ```

7. Inside the container, run the command to add a workflow:
   ```bash
   ./main.sh add_wf --site_config_file /fw/perlmutter_config.yaml
   ```

8. The system will process your request and provide a workflow ID. Make note of this ID for future reference or management of the workflow.

Remember to replace placeholder values (like paths and SSH keys) with your actual data. Always ensure that your site configuration file contains the correct and up-to-date information before adding a workflow.

**Note:** It is strongly recommended to use only one container to manipulate multiple launches of JRMs.

## Configuration

1. Create a site-specific configuration file based on the template:


```1:32:fw-lpad/FireWorks/jrm_launcher/site_config_template.yaml
slurm:
  nodes: {{int}}                 # Number of nodes, e.g., 1
  constraint: {{str}}            # Constraint for SLURM, e.g., "cpu" or "ejfat"
  walltime: {{str}}              # Walltime in HH:MM:SS format, e.g., "00:30:00"
  qos: {{str}}                   # Quality of Service, e.g., "normal" or "debug"
  account: {{str}}               # Account name, e.g., "m3792"
  {% if reservation %}reservation: {{str}}{% endif %}  # Optional reservation, leave empty if not used

jrm:
  nodename: {{str}}              # The name of the node, e.g., "vk-ornl"
  site: {{str}}                  # Site name, e.g., "ornl"
  control_plane_ip: {{str}}      # Control plane IP, e.g., "jiriaf2302"
  apiserver_port: {{int}}        # API server port, e.g., 38687
  kubeconfig: {{str}}            # Path to the kubeconfig file, e.g., "/path/to/kubeconfig"
  image: {{str}}                 # Docker image, e.g., "docker:jlabtsai/vk-cmd:main"
  {% if vkubelet_pod_ips %}vkubelet_pod_ips:            # List of vkubelet pod IPs
  {% for ip in vkubelet_pod_ips %}
    - {{str}}                   # IP address, e.g., "172.17.0.1"
  {% endfor %}{% endif %}
  {% if custom_metrics_ports %}custom_metrics_ports:    # List of custom metrics ports
  {% for port in custom_metrics_ports %}
    - {{int}}                   # Port number, e.g., 1234
  {% endfor %}{% endif %}
  config_class: {{str}}           # Configuration class to use, e.g., "perlmutter", "ornl", or "test"

ssh:
  remote_proxy: {{str}}          # SSH remote proxy, e.g., "perlmutter" or "none"
  remote: {{str}}                # SSH remote address, e.g., "jlabtsai@128.55.64.13"
  ssh_key: {{str}}               # Path to SSH key, e.g., "$HOME/.ssh/nersc"
  {% if password %}password: {{str}}{% endif %}         # Optional password, encoded in base64
  {% if build_script %}build_script: {{str}}{% endif %} # Optional build script for SSH, e.g., "./build-ssh-ornl.sh"

```


2. Save your configuration file with a meaningful name, e.g., `perlmutter_config.yaml`.

## Usage

The main entry point for the JRM Launcher is the `main.sh` script. This script should be used to execute various actions:

```bash
./main.sh <action> [options]
```

Available actions:

1. `add_wf`: Add a new workflow
2. `delete_wf`: Delete an existing workflow
3. `delete_ports`: Delete ports in a specified range
4. `connect`: Establish various connections (db, apiserver, metrics, custom_metrics)

### Examples

1. Add a new workflow:
```bash
./main.sh add_wf --site_config_file /path/to/perlmutter_config.yaml
```

2. Delete a workflow:
```bash
./main.sh delete_wf --fw_id 12345
```

3. Delete ports in a range:
```bash
./main.sh delete_ports --start 10000 --end 20000
```

4. Connect to the database:
```bash
./main.sh connect --connect_type db --site_config_file /path/to/perlmutter_config.yaml
```

5. Connect to the API server:
```bash
./main.sh connect --connect_type apiserver --port 35679 --site_config_file /path/to/perlmutter_config.yaml
```

6. Connect to the metrics server:
```bash
./main.sh connect --connect_type metrics --port 10001 --nodename vk-node-1 --site_config_file /path/to/perlmutter_config.yaml
```

7. Connect to custom metrics:
```bash
./main.sh connect --connect_type custom_metrics --mapped_port 20001 --custom_metrics_port 8080 --nodename vk-node-1 --site_config_file /path/to/perlmutter_config.yaml
```

## Main Components

1. `gen_wf.py`: Contains the `MainJrmManager` class, which is responsible for adding and deleting workflows, as well as managing connections.

2. `launch.py`: Implements the `JrmManager` class, which handles the creation and launching of JRM scripts.

3. `site_config.py`: Defines site-specific configurations and implementations for different computing environments.

4. `ssh.py`: Manages SSH connections and port forwarding.

5. `task.py`: Handles the creation of JRM scripts and management of ports.

6. `manage_port.py`: Provides functionality for finding and deleting ports associated with workflows.

## Logs

Logs for various operations are stored in the directory specified by `LOG_PATH` in `__init__.py`. Check these logs for detailed information about executed commands and their results.

## Customization

To add support for a new computing environment:

1. Create a new subclass of `BaseSiteConfig` in `site_config.py`.
2. Implement the required methods for the new environment.
3. Add the new configuration class to the `SITE_CONFIGS` dictionary in `site_config.py`.

## Troubleshooting

- If you encounter SSH connection issues, check the logs in the `LOG_PATH` directory for more information.
- Ensure that the configuration file is correctly formatted and contains all required fields.
- Verify that the necessary ports are available and not blocked by firewalls.

For more detailed information about each component, refer to the inline documentation in the respective Python files.
