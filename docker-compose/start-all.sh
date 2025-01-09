#!/bin/bash

# Start the SSH connections service
./start-ssh-connections.sh

# Start the containers
echo "Starting Docker containers..."
docker-compose up -d

echo "Services started" 