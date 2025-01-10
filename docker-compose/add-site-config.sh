#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 /path/to/your/config.yaml"
    exit 1
fi

CONFIG_PATH=$1
CONFIG_NAME=$(basename "$CONFIG_PATH")

# Copy directly into the container
docker cp "$CONFIG_PATH" "jrm-fw-lpad:/fw/site_configs/$CONFIG_NAME"

echo "Added $CONFIG_NAME to container's site_configs directory"
echo "The configuration is now available at /fw/site_configs/$CONFIG_NAME" 