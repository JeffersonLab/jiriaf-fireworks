#!/bin/bash

# Run /fw/create-ssh-connections/jrm-create-ssh-connections 
/fw/create-ssh-connections/jrm-create-ssh-connections &

# Define a function to display help
function display_help {
    echo "Usage: ./launch-jrms.sh [command] [options]"
    echo "Commands:"
    echo "  add_wf           Add a workflow to the launchpad. Requires the site-specific configuration file to be set."
    echo "  get_wf           Get workflows from the launchpad."
    echo "  delete_wf        Delete workflows from the launchpad. Requires one or more workflow IDs."
    echo "  delete_ports     Delete ports from the launchpad. Requires additional arguments for the start and end ports."
    echo "  connect          Establish a connection (db, apiserver, metrics, custom_metrics)."
    echo "  shell            Open an IPython shell and initialize LaunchPad and LOG_PATH."
    exit 0
}

# Define a function to handle invalid arguments
function handle_invalid_arg {
    echo "Invalid argument. Please use add_wf, get_wf, delete_wf, delete_ports, connect, or shell."
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
            echo "Please provide a site-specific configuration file to add a workflow. Example: ./launch-jrms.sh add_wf /path/to/site_config.yaml"
            exit 1
        fi
        python /fw/jrm_launcher/gen_wf.py add_wf --site_config_file "$2"
        ;;
    get_wf)
        lpad -l /fw/util/my_launchpad.yaml get_wflows -t 
        ;;
    delete_wf)
        if [ -z "$2" ]; then
            echo "Please provide one or more Firework IDs to delete. Example: ./launch-jrms.sh delete_wf 1 2 3"
            exit 1
        fi
        # Loop through all provided Firework IDs and delete each one
        for fw_id in "${@:2}"; do
            python /fw/jrm_launcher/gen_wf.py delete_wf --fw_id "$fw_id"
        done
        ;;
    delete_ports)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Please provide start and end ports to delete. Example: ./launch-jrms.sh delete_ports 8000 8100"
            exit 1
        fi
        python /fw/jrm_launcher/gen_wf.py delete_ports --start "$2" --end "$3"
        ;;
    connect)
        if [ -z "$2" ]; then
            echo "Please specify a connect type (db, apiserver, metrics, custom_metrics)."
            exit 1
        fi
        case "$2" in
            db)
                python /fw/jrm_launcher/gen_wf.py connect --site_config_file "$3" --connect_type db
                ;;
            apiserver)
                if [ -z "$4" ]; then
                    echo "Please provide a port number for the apiserver connection. Example: ./launch-jrms.sh connect apiserver /path/to/site_config.yaml 8000"
                    exit 1
                fi
                python /fw/jrm_launcher/gen_wf.py connect --site_config_file "$3" --connect_type apiserver --port "$4"
                ;;
            metrics)
                if [ -z "$4" ] || [ -z "$5" ]; then
                    echo "Please provide a port number and nodename for the metrics connection. Example: ./launch-jrms.sh connect metrics /path/to/site_config.yaml 8000 nodename"
                    exit 1
                fi
                python /fw/jrm_launcher/gen_wf.py connect --site_config_file "$3" --connect_type metrics --port "$4" --nodename "$5"
                ;;
            custom_metrics)
                if [ -z "$4" ] || [ -z "$5" ] || [ -z "$6" ]; then
                    echo "Please provide a mapped port, custom metrics port, and nodename for the custom metrics connection. Example: ./launch-jrms.sh connect custom_metrics /path/to/site_config.yaml 8000 8100 nodename"
                    exit 1
                fi
                python /fw/jrm_launcher/gen_wf.py connect --site_config_file "$3" --connect_type custom_metrics --mapped_port "$4" --custom_metrics_port "$5" --nodename "$6"
                ;;
            *)
                echo "Invalid connect type. Please choose from db, apiserver, metrics, custom_metrics."
                exit 1
                ;;
        esac
        ;;
    shell)
        cd /fw
        ipython -i -c "from fireworks import LaunchPad; LPAD = LaunchPad.from_file('/fw/util/my_launchpad.yaml'); LOG_PATH = '/fw/logs/'; print('LaunchPad and LOG_PATH initialized.')"
        ;;
    *)
        handle_invalid_arg
        ;;
esac
