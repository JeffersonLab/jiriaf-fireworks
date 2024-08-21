#!/bin/bash

# Define a function to display help
function display_help {
    echo "Usage: ./main.sh [command] [options]"
    echo "Commands:"
    echo "  add_wf       Add a workflow to the launchpad. Requires environment variables SITE (perlmutter or ornl) to be set."
    echo "  get_wf       Get workflows from the launchpad"
    echo "  delete_wf    Delete workflows from the launchpad. Requires an additional argument for the workflow id."
    echo "  delete_ports Delete ports from the launchpad. Requires additional arguments for the start and end ports."
    echo "  lpad         Run lpad commands. Requires additional arguments for the lpad command."
    exit 0
}

# Define a function to handle invalid arguments
function handle_invalid_arg {
    echo "Invalid argument. Please use add_wf, get_wf, delete_wf, delete_ports, or lpad."
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
        if [ -z "$SITE" ]; then
            echo "Please set the SITE environment variable (perlmutter or ornl)."
            exit 1
        fi
        /fw/create_config.sh || { echo "/fw/create_config.sh failed"; exit 1; }
        python /fw/gen_wf.py add_wf --site "$SITE"
        ;;
    get_wf)
        lpad -l /fw/util/my_launchpad.yaml get_wflows -t 
        ;;
    delete_wf)
        if [ -z "$2" ]; then
            echo "Please provide a Firework ID to delete."
            exit 1
        fi
        if [ -z "$SITE" ]; then
            echo "Please set the SITE environment variable (perlmutter or ornl)."
            exit 1
        fi
        python /fw/gen_wf.py delete_wf --fw_id "$2" --site "$SITE"
        ;;
    delete_ports)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Please provide start and end ports to delete."
            exit 1
        fi
        if [ -z "$SITE" ]; then
            echo "Please set the SITE environment variable (perlmutter or ornl)."
            exit 1
        fi
        python /fw/gen_wf.py delete_ports --start "$2" --end "$3" --site "$SITE"
        ;;
    lpad)
        lpad -l /fw/util/my_launchpad.yaml "${@:2}"
        ;;
    *)
        handle_invalid_arg
        ;;
esac
