#!/bin/bash

# Stop the containers
if command -v docker &> /dev/null; then
    if docker compose version &> /dev/null; then
        docker compose down
    else
        docker-compose down
    fi
else
    echo "Error: Docker is not installed"
    exit 1
fi

# Kill the SSH connections service
pkill -f "jrm-create-ssh-connections"

# Start everything again
./start-all.sh 