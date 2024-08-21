#!/bin/bash

# Define a function to display help
function display_help {
    echo "Usage: ./main.sh [command] [options]"
    echo "Commands:"
    echo "  add_wf       Add a workflow to the launchpad. Requires the site-specific configuration file to be set."
    echo "  get_wf       Get workflows from the launchpad."
    echo "  delete_wf    Delete workflows from the launchpad. Requires one or more workflow IDs."
    echo "  delete_ports Delete ports from the launchpad. Requires additional arguments for the start and end ports."
    echo "  shell        Open an IPython shell and initialize LaunchPad and LOG_PATH."
    exit 0
}

# Define a function to handle invalid arguments
function handle_invalid_arg {
    echo "Invalid argument. Please use add_wf, get_wf, delete_wf, delete_ports, or shell."
    display_help
    exit 1
}

# Check if no arguments were provided or if help was requested
if [ -z "$1" ] || [ "$1" == "help" ] || [ "$1" == "-h" ]; then
    display_help
fi

# Handle the provided argument
case "$1" in
    add_wf)
        if [ -z "$2" ]; then
            echo "Please provide a site-specific configuration file to add a workflow."
            exit 1
        fi
        python /fw/jrm_launcher/gen_wf.py add_wf --site_config_file "$2"
        ;;
    get_wf)
        lpad -l /fw/util/my_launchpad.yaml get_wflows -t 
        ;;
    delete_wf)
        if [ -z "$2" ]; then
            echo "Please provide one or more Firework IDs to delete."
            exit 1
        fi
        # Loop through all provided Firework IDs and delete each one
        for fw_id in "${@:2}"; do
            python /fw/jrm_launcher/gen_wf.py delete_wf --fw_id "$fw_id"
        done
        ;;
    delete_ports)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Please provide start and end ports to delete."
            exit 1
        fi
        python /fw/jrm_launcher/gen_wf.py delete_ports --start "$2" --end "$3"
        ;;
    shell)
        cd /fw
        ipython -i -c "from fireworks import LaunchPad; LPAD = LaunchPad.from_file('/fw/util/my_launchpad.yaml'); LOG_PATH = '/fw/logs/'; print('LaunchPad and LOG_PATH initialized.')"
        ;;
    *)
        handle_invalid_arg
        ;;
esac
