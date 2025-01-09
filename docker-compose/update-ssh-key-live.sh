#!/bin/bash

# Ensure proper permissions on the SSH key
chmod 600 ~/.ssh/nersc

# Update the symlink in the container
docker exec jrm-fw-lpad bash -c '
  cd /root/.ssh &&
  if [ -L nersc ]; then
    rm nersc
  fi &&
  ln -s nersc_new nersc &&
  chmod 600 nersc
'

echo "SSH key updated successfully" 