#!/bin/bash

# Check if the service is already running
if pgrep -f "jrm-create-ssh-connections" > /dev/null; then
    echo "SSH connections service is already running"
    if curl -s http://localhost:8888/health > /dev/null; then
        echo "Service is healthy"
        exit 0
    else
        echo "Stopping existing service..."
        pkill -f "jrm-create-ssh-connections"
        sleep 2
    fi
fi

# Start the SSH connections binary
cd ../fw-lpad/create-ssh-connections
echo "Starting SSH connections service..."
./jrm-create-ssh-connections > ssh-connections.log 2>&1 &
PID=$!

# Wait for the service to be ready
echo "Waiting for SSH connections service to start..."
for i in {1..30}; do
    if ! ps -p $PID > /dev/null; then
        echo "Error: SSH connections service crashed. Check ssh-connections.log for details"
        cat ssh-connections.log
        exit 1
    fi

    if curl -s http://localhost:8888/health > /dev/null; then
        echo "SSH connections service is ready"
        exit 0
    fi
    echo -n "."
    sleep 1
done

echo
echo "Error: SSH connections service failed to respond to health check"
echo "Process is still running (PID: $PID)"
echo "Log contents:"
cat ssh-connections.log
kill $PID
exit 1 