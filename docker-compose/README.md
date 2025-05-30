# Docker Compose Setup for JRM Launcher

This directory contains the Docker Compose configuration for running JRM Launcher and its required MongoDB database.

## Prerequisites

- Docker
- Docker Compose
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

3. Add your site configuration:
   ```bash
   ./add-site-config.sh /path/to/your/config.yaml
   ```

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

Note: To add new configuration files to the container:
```bash
# Add a new site configuration
./add-site-config.sh /path/to/your/config.yaml
```
The configuration will be immediately available in the container.

## Usage

To start the services:

```bash
./start-all.sh
```

The startup script will automatically pull the latest versions of the images before starting the containers.

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

To update the ORNL account name:

```bash
# Update the account name in build-ssh-ornl.sh
./update-ornl-account.sh your_account_name
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