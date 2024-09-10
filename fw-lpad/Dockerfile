# Use an existing docker image as a base
FROM python:3.9

# Install necessary tools including SSH client
RUN apt-get update && apt-get install -y \ 
    net-tools \
    openssh-client \
    expect \
    lsof \
    vim \
    less \
    && rm -rf /var/lib/apt/lists/*

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

# Copy all files in the FireWorks directory to the container but keep the directory structure intact 
COPY FireWorks/jrm_launcher /fw/jrm_launcher
COPY FireWorks/main.sh /fw/main.sh

COPY create-ssh-connections/jrm-create-ssh-connections /fw/jrm-create-ssh-connections
COPY aux /fw/aux

# Change the working directory
WORKDIR /fw

# Copy the entrypoint script into the image
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]