#!/bin/bash

START_TIME=$SECONDS

sudo apt-get -y update
sudo apt-get -y install python3-pip
sudo apt-get -y install python3-pil
sudo apt-get -y install python3-numpy
sudo pip3 install RPi.GPIO
sudo pip3 install spidev

sudo raspi-config nonint do_spi 0

echo "We must reboot before the changes in this script take effect."
read -p "Do you want to reboot now? (Y/n) " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
  sudo reboot
else
  exit 1
fi

ELAPSED_TIME=$(($SECONDS - $START_TIME))
echo "Script finished. Elapsed time: $ELAPSED_TIME seconds"
