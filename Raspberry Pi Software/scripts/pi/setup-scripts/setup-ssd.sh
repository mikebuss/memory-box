#!/bin/bash

# This script sets up a solid state drive (SSD) on a Raspberry Pi.
# It creates a mount point and mounts the drive, checks if the drive is mounted correctly,
# adds an entry to fstab if not present, and remounts the drive based on the new fstab.

# Create mount point and mount drive
sudo mkdir -p /mnt/sda2
sudo mount -t ext4 UUID=19d4a257-01a1-4646-9bef-a3e868980368 /mnt/sda2

# Check if the drive is mounted correctly
if df -h | grep -q '/mnt/sda2'; then
    echo "Drive is mounted correctly."
else
    echo "Failed to mount the drive. Exiting."
    exit 1
fi

# Line to be added if not present
LINE="/dev/sda2 /mnt/sda2 ext4 defaults 0 0"

# Check if line exists
if ! grep -qF "$LINE" /etc/fstab; then
    echo "Adding fstab entry for /dev/sda2."
    echo "$LINE" | sudo tee -a /etc/fstab
else
    echo "/dev/sda2 already exists in fstab."
fi

# Remount drive based on the new fstab
echo "Remounting drive based on new fstab..."
sudo umount /mnt/sda2
sudo mount -a

sudo mkdir /mnt/sda2/images
sudo mkdir /mnt/sda2/logs
sudo mkdir /mnt/sda2/tmp

sudo chown mikebuss:mikebuss /mnt/sda2/images;
sudo chown mikebuss:mikebuss /mnt/sda2/logs;
sudo chown mikebuss:mikebuss /mnt/sda2/tmp;

echo "Done."
