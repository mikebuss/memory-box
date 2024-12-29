#!/bin/bash

START_TIME=$SECONDS

sudo raspi-config nonint do_i2c 0

i2cdetect -y 1
i2cdump -y 1 0x32
i2cdump -y 1 0x75

curl http://cdn.pisugar.com/release/pisugar-power-manager.sh | sudo bash

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
