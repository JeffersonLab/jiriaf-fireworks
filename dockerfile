# Use an existing docker image as a base
FROM python:3.10

# Install necessary tools including SSH client and netstat
RUN apt-get update && apt-get install -y net-tools openssh-client expect

# Create a directory for SSH configuration
RUN mkdir -p /root/.ssh

# Copy the SSH config and script for SSH setup (adjust these if necessary)
COPY build-ssh-ornl.sh /root/build-ssh-ornl.sh
RUN chmod +x /root/build-ssh-ornl.sh

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Install ipython
RUN pip install ipython

# Create log directory and copy necessary files
RUN mkdir -p /fw/logs
COPY FireWorks/util /fw/util
COPY main /fw/main

# Copy all files in the FireWorks directory to the container but keep the directory structure intact 
COPY FireWorks/jrm_launcher /fw/jrm_launcher
COPY FireWorks/launch-jrms.sh /fw/launch-jrms.sh

COPY create-ssh-connections/* /fw/create-ssh-connections/

# Set the entrypoint to the launch script
ENTRYPOINT ["/fw/launch-jrms.sh"]
