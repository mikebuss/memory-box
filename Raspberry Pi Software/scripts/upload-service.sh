#!/bin/zsh

# Upload scripts from my development machine to the Raspberry Pi

LOCAL_DIR="./pi/services"
REMOTE_USER="mikebuss"
REMOTE_HOST="192.168.1.8"
REMOTE_DIR="~/services"

# Sync the contents
for item in $LOCAL_DIR/*; do
  rsync -avz --progress "$item" $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR
done
