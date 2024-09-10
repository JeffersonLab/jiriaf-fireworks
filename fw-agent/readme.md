# FireWorks Agent Setup

This guide explains how to set up a FireWorks agent on remote compute sites using a Python environment and configuration files.

## Prerequisites

- Python 3.9
- Access to remote compute sites (e.g., ORNL, NERSC)

## Setup Instructions

1. Create a new directory for your FireWorks agent:

```bash
mkdir fw-agent
cd fw-agent
```

2. Copy the `requirements.txt` file into this directory:


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


3. Create a virtual environment and activate it:
Require python 3.9
```bash
python3 -m venv venv
source venv/bin/activate
```

4. Install the required packages:

```bash
pip install -r requirements.txt
```

5. Copy the `fw_config` directory and its contents into your `fw-agent` directory. This directory contains site-specific configuration files for different compute environments.


6. Configure the FireWorks files for ORNL:

   a. `my_fworker.yaml`: Defines the FireWorks worker settings
   ```yaml
   category: < this should be the same as the site name in fw-lpad/FireWorks/jrm_launcher/site_config_template.yaml >  
   name: <recommended to be the same as the category>
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

   d. `queue_template.yaml`: Template for job submission scripts. 

   Notice that the variables in "slurm:" in [fw-lpad/FireWorks/jrm_launcher/site_config_template.yaml](fw-lpad/FireWorks/jrm_launcher/site_config_template.yaml) overwrites the ones in this template. Other than that, the rest of the variables are defined here.

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


## Running FireWorks Agent

To run the FireWorks agent on a remote compute site:

1. SSH into the remote compute site.

2. Navigate to your `fw-agent` directory.

3. Activate the virtual environment:

```bash
source venv/bin/activate
```

4. Run the FireWorks qlaunch command:

```bash
qlaunch -r rapidfire
```

This command will start the FireWorks rapid-fire mode, which will continuously pull and run jobs from the LaunchPad.

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