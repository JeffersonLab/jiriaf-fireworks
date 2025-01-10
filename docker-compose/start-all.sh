#!/bin/bash

# Pull the latest images
echo "Pulling latest images..."
docker compose pull

# Start the containers
echo "Starting Docker containers..."
if command -v docker &> /dev/null; then
    if docker compose version &> /dev/null; then
        docker compose up -d --pull always
    elif command -v docker-compose &> /dev/null; then
        docker-compose up -d --pull always
    else
        echo "Error: Neither 'docker compose' nor 'docker-compose' command is available"
        exit 1
    fi
else
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

echo "Services started" 