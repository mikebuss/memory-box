#!/bin/bash

# Define the path to the services directory
SERVICE_DIR="$HOME/services"

# Check if the service directory exists
if [[ ! -d $SERVICE_DIR ]]; then
  echo "Service directory $SERVICE_DIR does not exist."
  exit 1
fi

# Loop through each service folder and stop the service
for service_folder in $SERVICE_DIR/*; do
  if [[ -d $service_folder ]]; then
    service_name=$(basename $service_folder)
    echo "Stopping service $service_name..."
    
    # Stop the service
    sudo systemctl stop $service_name

    echo "Service $service_name stopped."
  fi
done

echo "All services stopped."
