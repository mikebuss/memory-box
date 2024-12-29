#!/bin/bash

set -e
set -x

START_TIME=$SECONDS

# Update the system
sudo apt -y update
sudo apt -y full-upgrade
sudo apt -y upgrade
sudo apt -y install rsync

# Install all the necessary packages
sudo apt -y install python3-pip
sudo apt -y install i2c-tools
sudo apt -y install libmagickwand-dev

# Install Bluetooth tools
sudo apt -y install bluetooth bluez-tools bluez
sudo systemctl enable bluetooth

# Install development packages
sudo apt -y install vim
sudo apt -y install git

# Install the Python packages
pip install smbus
pip install Wand
pip install Pillow

pip install psycopg2
pip install Flask
pip install schedule

### TODO: Is this necessary?
cd ~
sudo pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo python3 raspi-blinka.py
# --------------------------



# pip install adafruit_fingerprint
sudo pip3 install adafruit-circuitpython-fingerprint

pip install bluepy
pip install bluez-peripheral

# Enable I2C for the battery communication
sudo raspi-config nonint do_i2c 0

# Enable GPIO26 as the "safe shutdown" pin
LINE_TO_ADD="dtoverlay=gpio-shutdown,gpio_pin=26"
FILE_PATH="/boot/config.txt"

# Check if the line already exists
if grep -Fxq "$LINE_TO_ADD" $FILE_PATH; then
  echo "Skipping enabling GPIO26 for shutdown. This has already been done."
else
  # Append the line to the file
  echo "$LINE_TO_ADD" | sudo tee -a $FILE_PATH
  echo "Enabled GPIO26 for shutdown."
fi

ELAPSED_TIME=$(($SECONDS - $START_TIME))
echo "Script finished. Elapsed time: $ELAPSED_TIME seconds"
