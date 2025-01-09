#!/bin/bash

# Build and start the SSH connections binary
cd ../fw-lpad/create-ssh-connections
./jrm-create-ssh-connections &

# Wait for the service to be ready
echo "Waiting for SSH connections service to start..."
for i in {1..30}; do
    if curl -s http://localhost:8888/health > /dev/null; then
        echo "SSH connections service is ready"
        exit 0
    fi
    sleep 1
done

echo "Error: SSH connections service failed to start"
exit 1 