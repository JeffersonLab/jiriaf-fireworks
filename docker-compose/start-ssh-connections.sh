#!/bin/bash

# Kill any existing instances
pkill -f "jrm-create-ssh-connections" 2>/dev/null

# Start the SSH connections binary
cd ../fw-lpad/create-ssh-connections
echo "Starting SSH connections service..."
./jrm-create-ssh-connections > ssh-connections.log 2>&1 &

echo "SSH connections service started in background"
exit 0 