#!/bin/bash

set -e
set -x

echo "Are you sure you want to drop the table and re-create it? All data will be lost! (Y/N)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
    psql -U postgres -h localhost -d postgres -a -f media-schema.pql
    echo "Table has been dropped and re-created."
else
    echo "Operation aborted."
fi
