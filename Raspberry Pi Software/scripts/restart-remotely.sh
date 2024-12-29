#!/bin/zsh

# Upload scripts from my development machine to the Raspberry Pi

LOCAL_DIR="./pi/"
REMOTE_USER="mikebuss"
REMOTE_HOST="192.168.1.8"
REMOTE_DIR="~/"

ssh $REMOTE_USER@$REMOTE_HOST "sudo systemctl restart memorybox"

