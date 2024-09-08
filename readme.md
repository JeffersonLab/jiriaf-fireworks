# JRM Launcher

JRM Launcher is a tool designed to manage and launch Job Resource Manager (JRM) instances across various computing environments, with a focus on facilitating complex network connections in distributed computing setups.

## Network Architecture

The core functionality of JRM Launcher revolves around managing network connections between different components of a distributed computing environment. The network architecture is visually represented in the [jrm-network](jrm-network.png) file included in this repository.

[![JRM Network Diagram](markdown/jrm-network.png)](markdown/jrm-network.png)

This diagram illustrates the key components and connections managed by JRM Launcher (JRM-FW), including:

1. SSH connections to remote servers
2. Port forwarding for various services
3. Connections to databases, API servers, and metrics servers
4. Workflow management across different computing nodes

JRM Launcher acts as a central management tool, orchestrating these connections to ensure smooth operation of distributed workflows and efficient resource utilization.

## Key Features

- Workflow management
- Flexible connectivity to various services
- Site-specific configurations
- SSH integration and port forwarding
- Port management for workflows

## Setup and Usage

### Basic Usage of JRM-FW

To use JRM Launcher:

1. Ensure you have the necessary prerequisites installed.
2. Create a site-specific configuration file.
3. Use the [`main.sh`](fw-lpad/FireWorks/main.sh) script to execute desired actions.

For detailed information on prerequisites, configuration, usage examples, and customization, please refer to the comprehensive guide in the [fw-lpad readme](fw-lpad/readme.md) file of this repository.

### Remote Launch with FireWorks Agent (FW Agent)

JRM Launcher supports remote launch of JRMs using FireWorks agents, enabling efficient management of workflows across different computing environments. Key points:

- Set up FireWorks agents on remote compute sites
- Configure site-specific settings in the `fw_config` directory
- Use `qlaunch` command to start the FireWorks agent on remote sites

For detailed instructions on setting up and using FireWorks agents, refer to the [fw-agent readme](fw-agent/readme.md).

## Extensibility

JRM Launcher is designed to be easily extensible to support various computing environments. For information on how to add support for new environments, refer to the "Customization" section in the [fw-lpad readme](fw-lpad/readme.md) file.

## Troubleshooting

For troubleshooting tips and logging information, please consult the "Troubleshooting" section in the [fw-lpad readme](fw-lpad/readme.md) file.

By leveraging JRM Launcher, you can simplify the management of complex network connections in distributed computing environments, allowing you to focus on your workflows rather than infrastructure management.