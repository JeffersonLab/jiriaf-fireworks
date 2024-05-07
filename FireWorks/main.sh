#!/bin/bash

if [ "$1" == "help" ] || [ "$1" == "-h" ]; then
    echo "Usage: ./main.sh [command]"
    echo "Commands:"
    echo "  add_wf   Add a workflow to the launchpad. Requires environment variables to be set."
    echo "  get_wf       Get workflows from the launchpad"
    echo "  delete_wf    Delete workflows from the launchpad. Requires an additional argument for the workflow id."
    exit 0
fi

if [ "$1" == "add_wf" ]; then
    /fw/create_config.sh
    if [ $? -ne 0 ]; then
        echo "/fw/create_config.sh failed"
        exit 1
    fi
    python /fw/gen_wf.py
fi
elif [ "$1" == "get_wf" ]; then
    lpad -l /fw/my_launchpad.yaml get_wflows -t 
elif [ "$1" == "delete_wf" ]; then
    lpad -l /fw/my_launchpad.yaml delete_wflows -i $2
else
    echo "Invalid argument. Please use add_wf, get_wf, or delete_wf."
fi