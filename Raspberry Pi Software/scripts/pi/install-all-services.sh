#!/bin/bash

sudo mkdir /mnt/sda2/logs
sudo chown mikebuss:mikebuss /mnt/sda2/logs

# Loop through each service folder in ~/services
for service_folder in ~/services/*; do
    if [ -d "$service_folder" ]; then
        # Extract just the folder name to use as the service name
        service_name=$(basename $service_folder)
        
        echo "Installing $service_name..."
        
        # Add execute permission to the Python script
        chmod +x $service_folder/$service_name.py
        
        # Copy the systemd service file to the appropriate location
        sudo cp $service_folder/$service_name.service /etc/systemd/system/
        
        # Reload the systemd daemon to recognize the new service
        sudo systemctl daemon-reload
        
        # Enable the service to start on boot
        sudo systemctl enable $service_name
        
        # Start the service immediately
        sudo systemctl start $service_name
    fi
done

echo "All services have been installed, enabled, and started."
