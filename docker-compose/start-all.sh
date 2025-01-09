#!/bin/bash

# Function to cleanup on exit
cleanup() {
    if [ $? -ne 0 ]; then
        echo "Cleaning up..."
        docker-compose down
        pkill -f "jrm-create-ssh-connections"
    fi
}

trap cleanup EXIT

# Start the SSH connections service
./start-ssh-connections.sh
if [ $? -ne 0 ]; then
    echo "Failed to start SSH connections service"
    exit 1
fi

# Start the containers
echo "Starting Docker containers..."
docker-compose up -d

# Check if containers started successfully
if ! docker-compose ps | grep -q "Up"; then
    echo "Error: Failed to start containers"
    exit 1
fi

echo "All services started successfully" 