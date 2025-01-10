#!/bin/bash

# Update SSH files in container
docker exec jrm-fw-lpad bash -c '
  # Copy updated files from host
  cp -r /host_ssh/* /root/.ssh/
  
  # Set proper permissions
  chmod 700 /root/.ssh
  chmod 600 /root/.ssh/*
'

echo "SSH key updated successfully" 