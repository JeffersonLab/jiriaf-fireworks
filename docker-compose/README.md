# Docker Compose Setup for JRM Launcher

This directory contains the Docker Compose configuration for running JRM Launcher and its required MongoDB database.

## Prerequisites

- Docker
- Docker Compose
- Valid site configuration file
- SSH key for remote access

## Setup

1. Configure your site:
   - Use the default configuration in `site_configs/perlmutter.yaml` as a template
   - Create your own site configuration file in the `site_configs` directory
   - Update the `SITE_CONFIG` path in `.env` to point to your configuration file

2. Create required directories and files:
   - Create a logs directory or update the `LOGS_DIR` path in `.env`
   - Ensure you have a valid port_table.yaml file
   - Update the SSH key path in `.env` if needed

## Site Configuration

The `site_configs` directory contains YAML files for different computing sites. The default `perlmutter.yaml` provides a template for NERSC's Perlmutter system. To use a different site:

1. Create a new YAML file in the `site_configs` directory
2. Update the configuration for your site
3. Update the `SITE_CONFIG` variable in `.env` to point to your new configuration file

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

## Configuration

- MongoDB data is persisted in a named volume
- The MongoDB initialization script creates the required user and database
- JRM Launcher configuration is mounted from your local files
- Environment variables can be configured in the `.env` file

## Volumes

- `mongodb_data`: Persistent storage for MongoDB data
- Configuration files are mounted from your local system

## Networks

- MongoDB runs on a bridge network
- JRM Launcher uses host networking to facilitate SSH connections 