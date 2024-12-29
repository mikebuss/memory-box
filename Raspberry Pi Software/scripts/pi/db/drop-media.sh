#!/bin/bash

set -e
set -x

echo "Are you sure you want to delete all media and related data from the database? Type 'media' to confirm:"
read -r confirmation

if [[ "$confirmation" == "media" ]]; then
    psql -U postgres -h localhost -d postgres -c "
        DELETE FROM media_people;
        DELETE FROM media;
    "
    echo "Media and related data have been deleted from the database."
else
    echo "Operation aborted."
fi
