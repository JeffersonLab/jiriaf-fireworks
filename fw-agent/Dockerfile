# Use an official Ubuntu as the base image
FROM ubuntu:20.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV SLURM_VERSION=23.02.6
ENV SLURM_CONF=/home/slurm/slurm.conf

# Install dependencies for building SLURM and Python 3.9
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    curl \
    wget \
    sudo \
    vim \
    libmunge-dev \
    libmunge2 \
    munge \
    openssh-client \
    openssh-server \
    nfs-common \
    libssl-dev \
    libpam0g-dev \
    libmariadb-dev-compat \
    libmariadb-dev \
    perl \
    libswitch-perl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Add deadsnakes PPA for Python 3.9
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.9 python3.9-venv python3.9-dev python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Set Python 3.9 as the default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1

# Create the slurm user and its home directory
RUN useradd -m -d /home/slurm -s /bin/bash slurm && \
    mkdir -p /home/slurm && \
    chown slurm:slurm /home/slurm

# Copy the requirements.txt to the container
COPY requirements.txt /home/slurm/requirements.txt

# Install Python dependencies
RUN pip3 install --upgrade pip && \
    pip3 install -r /home/slurm/requirements.txt

# Download and compile SLURM from source
RUN wget https://download.schedmd.com/slurm/slurm-$SLURM_VERSION.tar.bz2 && \
    tar -xjf slurm-$SLURM_VERSION.tar.bz2 && \
    cd slurm-$SLURM_VERSION && \
    ./configure --prefix=/usr --sysconfdir=/etc/slurm-llnl && \
    make && make install && \
    cd .. && rm -rf slurm-$SLURM_VERSION slurm-$SLURM_VERSION.tar.bz2

# Create SLURM user and group if they do not exist
RUN groupadd -g 64030 slurm || true && \
    id -u slurm &>/dev/null || useradd -u 64030 -g slurm -c "SLURM workload manager" -s /bin/bash -d /var/lib/slurm slurm && \
    mkdir -p /var/lib/slurm && \
    chown slurm:slurm /var/lib/slurm

# Create SLURM and MUNGE directories
RUN mkdir -p /etc/slurm-llnl /var/spool/slurmd /var/log/slurm

# Configure MUNGE
RUN groupadd -f munge && \
    id -u munge &>/dev/null || useradd -r -g munge munge && \
    mkdir -p /etc/munge /var/lib/munge /var/log/munge && \
    chown -R munge:munge /etc/munge /var/lib/munge /var/log/munge

# Start MUNGE and SLURM services
CMD /etc/init.d/munge start && /usr/sbin/slurmd && /bin/bash

# Expose ports
EXPOSE 6817 6818 6819

COPY fw_config /fw_config

# Run bash shell by default
CMD ["bash"]
