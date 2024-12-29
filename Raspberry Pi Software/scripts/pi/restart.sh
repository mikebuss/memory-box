#!/bin/bash

sudo systemctl restart memorybox

sudo journalctl -u memorybox.service -f
