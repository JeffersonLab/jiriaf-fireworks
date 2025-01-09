#!/bin/bash

# Start the SSH connections service
./start-ssh-connections.sh

# Start the containers
echo "Starting Docker containers..."

# Try docker compose first, fall back to docker-compose
if command -v docker &> /dev/null; then
    if docker compose version &> /dev/null; then
        docker compose up -d
    elif command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        echo "Error: Neither 'docker compose' nor 'docker-compose' command is available"
        exit 1
    fi
else
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

echo "Services started" 