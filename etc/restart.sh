#!/bin/bash

if [ $# -gt 0 ]; then
    # Validate if the parameter is a positive integer
    if [[ $1 =~ ^[0-9]+$ ]]; then
        echo "Waiting for $1 seconds before restarting services..."
        sleep $1
    else
        echo "Invalid parameter. Please provide a positive integer for the wait time."
        exit 1
    fi
fi

sudo systemctl restart frame.service&
sudo systemctl restart kiosk.service&