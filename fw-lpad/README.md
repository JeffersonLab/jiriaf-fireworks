# JRM Launcher

JRM Launcher is a tool for managing and launching JRM (Job Resource Manager) instances on various computing environments.

## Prerequisites
- Have valid NERSC account, ORNL user account, or other remote computing site account
- MongoDB (for storing workflow of JRM launches)
- Kubernetes API server running
- Valid kubeconfig file for the Kubernetes cluster
- Python 3.9 (for developers)
  - Required Python packages (install via `pip install -r requirements.txt`)
- **NERSC SSH Key Setup:**
  - Copy the provided script to your `~/.ssh` directory:
    ```bash
    cp fw-lpad/aux/sshproxy.sh ~/.ssh/
    cd ~/.ssh
    chmod +x sshproxy.sh
    ./sshproxy.sh -u <your-username>
    ```
    This will generate your NERSC SSH key (`~/.ssh/nersc`). Follow the prompts to authenticate and generate your key.
- **NERSC SSH Config Setup:**
  - Set up your SSH config for NERSC by copying the example config:
    ```bash
    cp fw-lpad/aux/ssh_config ~/.ssh/config
    ```
    Edit `<your-username>` in the config to your NERSC username.

  This SSH config allows you to use hostnames like `login33` for Perlmutter login nodes, and will automatically connect through the DTN proxy.

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
       remote_proxy: perlmutter # keep it but this is not used
       remote: loginXX # where XX is the number of a login node on Perlmutter (e.g., login33)
       ssh_key: /root/.ssh/mykey 
       password:
       build_script:
     ```

3. Copy the kubeconfig file to the remote site:
   ```bash
   scp /path/to/local/kubeconfig user@remote:/path/to/remote/kubeconfig
   ```
   Update the `jrm.kubeconfig` in your site config to point to this remote location.

4. Set up MongoDB for storing Fireworks workflows:
   a. Create and start a MongoDB container:
      ```bash
      docker run -d -p 27017:27017 --name mongodb-container \
        -v $HOME/mongodb/data:/data/db mongo:latest
      ```
      This command starts a MongoDB container, maps port 27017, and mounts a volume for persistent data storage.

   b. Wait for MongoDB to start (about 10 seconds), then create a new database and user:
      ```bash
      docker exec -it mongodb-container mongosh --eval '
        db.getSiblingDB("< fireworks database name >").createUser({
          user: "< fireworks database username >",
          pwd: "< fireworks database password >",
          roles: [{role: "readWrite", db: "< fireworks database name >"}]
        })
      '
      ```
      This command creates a new database named `< fireworks database name >` with a user `< fireworks database username >` (password: `< fireworks database password >`) having read and write permissions.

   Note: The database information (name, username, and password) set up in this step will be used in your `my_launchpad.yaml`.

5. Prepare Fireworks config file `my_launchpad.yaml` base one the previously created database. (see [fw-agent readme](../fw-agent/readme.md))

6. Start the JRM Launcher container:
   ```bash
   export logs=/path/to/your/logs/directory
   docker run --name=jrm-fw-lpad -itd --rm --net=host \
     -v ./perlmutter_config.yaml:/fw/perlmutter_config.yaml \
     -v $logs:/fw/logs \
     -v `pwd`/port_table.yaml:/fw/port_table.yaml \
     -v $HOME/.ssh/nersc:/root/.ssh/nersc \
     -v `pwd`/my_launchpad.yaml:/fw/util/my_launchpad.yaml \
     jlabtsai/jrm-fw-lpad:main
   ```

7. Verify the container is running:
   ```bash
   docker ps
   ```

8. Log into the container:
   ```bash
   docker exec -it jrm-fw-lpad /bin/bash
   ```

9. Inside the container, run the command to add a workflow:
   ```bash
   ./main.sh add_wf /fw/perlmutter_config.yaml
   ```

10. The system will process your request and provide a workflow ID. Make note of this ID for future reference or management of the workflow.

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
  control_plane_ip: {{str}}      # Control plane IP, e.g., "jiriaf2302". This is just for the record
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
./main.sh add_wf /fw/perlmutter_config.yaml
```

2. Delete a workflow:
```bash
./main.sh delete_wf 12345
```

3. Delete ports in a range:
```bash
./main.sh delete_ports 10000 20000
```

4. Connect to the database:
```bash
./main.sh connect db /fw/perlmutter_config.yaml
```

5. Connect to the API server:
```bash
./main.sh connect apiserver 35679 /fw/perlmutter_config.yaml
```

6. Connect to the metrics server:
```bash
./main.sh connect metrics 10001 vk-node-1 /fw/perlmutter_config.yaml
```

7. Connect to custom metrics:
```bash
./main.sh connect custom_metrics 20001 8080 vk-node-1 /fw/perlmutter_config.yaml
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
