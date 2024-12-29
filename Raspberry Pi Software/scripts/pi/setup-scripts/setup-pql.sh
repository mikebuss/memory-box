#!/bin/bash
START_TIME=$SECONDS

# Install PostgreSQL
if sudo apt-get install -y postgresql postgresql-contrib; then
  echo "PostgreSQL installed successfully."
else
  echo "Failed to install PostgreSQL. Exiting."
  exit 1
fi

# Define variables
LINE_TO_ADD="host     all     all     192.168.1.0/24     trust"
PG_HBA="/etc/postgresql/13/main/pg_hba.conf"
PG_CONF="/etc/postgresql/13/main/postgresql.conf"
NEW_DATA_DIR="/mnt/sda2/postgresql"
OLD_DATA_DIR="/var/lib/postgresql/13/main"

# Update pg_hba.conf for remote access
if sudo grep -Fxq "$LINE_TO_ADD" $PG_HBA; then
  echo "The line already exists in pg_hba.conf. No changes made."
else
  echo "$LINE_TO_ADD" | sudo tee -a $PG_HBA && echo "Updated pg_hba.conf."
fi

# Update postgresql.conf to allow remote connections
SEARCH_PATTERN="#listen_addresses = 'localhost'"
REPLACE_PATTERN="listen_addresses = '*'"

if sudo grep -Fq "$SEARCH_PATTERN" $PG_CONF; then
  sudo sed -i "s/$SEARCH_PATTERN/$REPLACE_PATTERN/g" $PG_CONF && echo "Updated postgresql.conf."
else
  echo "postgresql.conf already updated."
fi

ELAPSED_TIME=$(($SECONDS - $START_TIME))
echo "Elapsed time: $ELAPSED_TIME seconds"


# Move Postgresql

if [ ! -d "/mnt/sda2/pg" ]; then
echo "Destination directory does not exist. Moving database..."
  sudo rsync -av /var/lib/postgresql /mnt/sda2/pg
else
  echo "Destination directory already exists. Skipping rsync."
fi

# Backup the original configuration file
sudo cp /etc/postgresql/13/main/postgresql.conf /etc/postgresql/13/main/postgresql.conf.bak

# Use sed to edit the file in place, modifying the data_directory line
sudo sed -i "s|data_directory = '[^']*'|data_directory = '/mnt/sda2/pg/postgresql/13/main'|" /etc/postgresql/13/main/postgresql.conf

echo "The data_directory has been updated in /etc/postgresql/13/main/postgresql.conf"

