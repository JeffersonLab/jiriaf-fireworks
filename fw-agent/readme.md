# FireWorks Agent Setup on Remote Compute Sites

This guide explains how to set up a FireWorks agent on remote compute sites using a Python environment and configuration files.

## Prerequisites

- Python 3.9 (available on the remote compute site)
- Access to remote compute sites (e.g., ORNL, NERSC)

## Remote Setup Instructions

**Important: Perform all the following steps on the remote compute site.**

1. SSH into the remote compute site.

2. Create a new directory for your FireWorks agent:

    ```bash
    mkdir fw-agent
    cd fw-agent
    ```

3. Copy the `requirements.txt` file into this directory (you may need to transfer it from your local machine):

    ```1:21:fw-agent/requirements.txt
    click==8.0.3
    FireWorks==1.9.7
    Flask==2.0.2
    flask-paginate==2021.12.28
    gunicorn==20.1.0
    itsdangerous==2.0.1
    Jinja2==3.0.3
    MarkupSafe==2.0.1
    monty==2023.11.3
    prettytable==3.10.0
    pymongo==3.12.3
    python-dateutil==2.8.2
    ruamel.yaml==0.17.20
    ruamel.yaml.clib==0.2.6
    six==1.16.0
    tabulate==0.8.9
    tqdm==4.62.3
    wcwidth==0.2.13
    Werkzeug==2.0.2
    requests==2.26.0

    ```

4. Create a virtual environment and activate it (using Python 3.9 available on the remote site):

    ```bash
    python3.9 -m venv jrm_launcher  
    source jrm_launcher/bin/activate
    ```

5. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

6. Create the `fw_config` directory and the necessary configuration files:

    ```bash
    mkdir fw_config
    cd fw_config
    ```

   a. `my_fworker.yaml`: Defines the FireWorks worker settings
   ```yaml
   category: < this must be the same as the site name in fw-lpad/FireWorks/jrm_launcher/site_config_template.yaml >  
   name: < recommended to be the same as the category >
   query: '{}'
   ```

   b. `my_qadapter.yaml`: Configures the queue adapter for job submission
   ```yaml
   _fw_name: CommonAdapter
   _fw_q_type: SLURM
   _fw_template_file: < path to the queue_template.yaml >
   rocket_launch: rlaunch -c < path to the fw_config > singleshot
   nodes: 
   walltime:
   constraint:
   account:
   job_name:
   logdir: < path to the logs >
   pre_rocket:
   post_rocket:
   ```

   c. `my_launchpad.yaml`: Specifies the LaunchPad connection details
   ```yaml
   host: localhost
   logdir: < path to the logs >
   mongoclient_kwargs: {}
   name: <fireworks database name >
   password: <fireworks database password>
   port: 27017
   strm_lvl: INFO
   uri_mode: false
   user_indices: []
   username: <fireworks database username>
   wf_user_indices: []
   ```
    Please refer to the created database in [fw-lpad](../fw-lpad/readme.md) and fill in the correct information.
    
   d. `queue_template.yaml`: Template for job submission scripts. 

   Notice that the variables in "slurm:" in [fw-lpad site_config_template.yaml](../fw-lpad/FireWorks/jrm_launcher/site_config_template.yaml) overwrites the ones in this template. Other than that, the rest of the variables are defined here.

    ```1:27:fw-agent/fw_config/ornl/queue_template.yaml

    #!/bin/bash -l

    #SBATCH --nodes=$${nodes}
    #SBATCH --ntasks=$${ntasks}
    #SBATCH --ntasks-per-node=$${ntasks_per_node}
    #SBATCH --cpus-per-task=$${cpus_per_task}
    #SBATCH --mem=$${mem}
    #SBATCH --gres=$${gres}
    #SBATCH --qos=$${qos}
    #SBATCH --time=$${walltime}
    #SBATCH --partition=$${queue}
    #SBATCH --account=$${account}
    #SBATCH --job-name=$${job_name}
    #SBATCH --license=$${license}
    #SBATCH --output=$${job_name}-%j.out
    #SBATCH --error=$${job_name}-%j.error
    #SBATCH --constraint=$${constraint}
    #SBATCH --reservation=$${reservation}


    $${pre_rocket}
    cd $${launch_dir}
    $${rocket_launch}
    $${post_rocket}

    # CommonAdapter (SLURM) completed writing Template

    ```

## Running FireWorks Agent on the Remote Site

To run the FireWorks agent on the remote compute site:

1. Ensure you're still connected to the remote compute site.

2. Navigate to your `fw-agent` directory on the remote site.

3. Activate the virtual environment:
    ```bash
    source jrm_launcher/bin/activate
    ```

4. Test the connection to the LaunchPad database:
    ```bash
    lpad -c <path to the fw_config> reset
    ```
    If you see the prompt "Are you sure? This will RESET your LaunchPad. (Y/N)", then your setup is correct and the connection is working. Type 'N' to cancel the reset operation.

5. Run the FireWorks qlaunch command:
    ```bash
    qlaunch -c <path to the fw_config> -r rapidfire
    ```
    Make sure you check `qlaunch -h` for more options.

This command will start the FireWorks rapid-fire mode on the remote site, which will continuously pull and run jobs from the LaunchPad.

## Site-Specific Configuration

The `fw_config` directory contains site-specific configuration files:

- `my_fworker.yaml`: Defines the FireWorks worker settings
- `my_qadapter.yaml`: Configures the queue adapter for job submission
- `my_launchpad.yaml`: Specifies the LaunchPad connection details
- `queue_template.yaml`: Template for job submission scripts

Ensure you use the correct configuration files for your target compute site.

## Troubleshooting

- Make sure your FireWorks LaunchPad is accessible from the remote compute site.
- Verify that the Python environment has all the necessary dependencies installed.

For more detailed information on FireWorks configuration and usage, refer to the [FireWorks documentation](https://materialsproject.github.io/fireworks/).