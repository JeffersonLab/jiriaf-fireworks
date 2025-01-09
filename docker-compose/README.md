# Docker Compose Setup for JRM Launcher

This directory contains the Docker Compose configuration for running JRM Launcher and its required MongoDB database.

## Prerequisites

- Docker
- Docker Compose
- Valid site configuration file
- SSH key for remote access

## Setup

1. Copy your site configuration file to this directory or update the `SITE_CONFIG` path in `.env`
2. Create a logs directory or update the `LOGS_DIR` path in `.env`
3. Ensure you have a valid port_table.yaml file
4. Update the SSH key path in `.env` if needed

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