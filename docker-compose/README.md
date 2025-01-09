# Docker Compose Setup for JRM Launcher

This directory contains the Docker Compose configuration for running JRM Launcher and its required MongoDB database.

## Prerequisites

- Docker
- Docker Compose
- Go (for building SSH connections binary)
- Valid site configuration file
- SSH key for remote access

## Setup

1. Make the startup scripts executable:
   ```bash
   chmod +x start-all.sh
   ```

2. Start the services:
   ```bash
   ./start-all.sh
   ```

3. Configure your site:
   - Use the default configuration in `site_configs/perlmutter.yaml` as a template
   - Create your own site configuration file in the `site_configs` directory
   - Update the `SITE_CONFIG_FILE` in `.env` to specify which configuration to use

4. Create required directories and files:
   - Create a logs directory or update the `LOGS_DIR` path in `.env`
   - Update the SSH key path in `.env` if needed

## Site Configuration

The `site_configs` directory contains YAML files for different computing sites. All configuration files
are available in the container at `/fw/site_configs/`. Example configurations are provided:

- `perlmutter-example.yaml`: Template for NERSC's Perlmutter system
- `ornl-example.yaml`: Template for ORNL's systems

To add your own configuration:

1. Create a new YAML file based on one of the examples
2. Update the configuration for your site

Note: The site_configs directory is mounted as read-only in the container. To add new
configuration files, add them to the site_configs directory on the host:
```bash
# Add a new site configuration
./add-site-config.sh /path/to/your/config.yaml
```
The configuration will be immediately available in the container.

Example site configuration structure:
```yaml
slurm:
  nodes: 1
  constraint: cpu
  walltime: 00:30:00
  qos: debug
  account: your_account
  reservation:

jrm:
  nodename: jrm-sitename
  site: sitename
  control_plane_ip: your_control_plane
  apiserver_port: your_port
  kubeconfig: path/to/kubeconfig
  image: docker:your/image:tag
  vkubelet_pod_ips:
    - your_pod_ip
  custom_metrics_ports: [port1, port2, port3, port4]
  config_class:

ssh:
  remote_proxy: user@proxy.site.domain
  remote: user@internal.site.ip
  ssh_key: /root/.ssh/your_key
  password:
  build_script:
```

## Usage

To start the services:

```bash
docker-compose up -d
```

To stop the services:

```bash
docker-compose down
```

To view logs:

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs mongodb
docker-compose logs jrm-fw-lpad
```

To update the SSH key without restarting the container:

```bash
# Update your SSH key in ~/.ssh/ and run:
./update-ssh-key-live.sh
```

Note: The host's SSH directory is mounted as read-only at /host_ssh in the container
and copied to the container's /root/.ssh with appropriate permissions. You can
update SSH keys anytime by modifying files in your ~/.ssh directory and running
the update-ssh-key-live.sh script.

## Configuration

- MongoDB data is persisted in a named volume
- The MongoDB initialization script creates the required user and database
- JRM Launcher configuration is mounted from your local files
- Environment variables can be configured in the `.env` file
- Port table is automatically managed during runtime
- SSH connections are managed by the jrm-create-ssh-connections binary

## Services

The setup includes two main services:

1. MongoDB (`mongodb`)
   - Stores workflow and task information
   - Persists data between restarts

2. JRM Launcher (`jrm-fw-lpad`)
   - Main workflow manager
   - Depends on MongoDB service
   - Connects to SSH service running on host
   - Uses host networking for remote connections

## Volumes

- `mongodb_data`: Persistent storage for MongoDB data
- Configuration files are mounted from your local system

## Networks

- MongoDB runs on a bridge network
- JRM Launcher uses host networking to facilitate SSH connections 