#!/bin/bash

# Start the SSH connections service
./start-ssh-connections.sh
if [ $? -ne 0 ]; then
    echo "Failed to start SSH connections service"
    exit 1
fi

# Start the containers
docker-compose up -d 