#!/bin/bash

set -e
set -x

psql -U postgres -h localhost -d postgres -c "SELECT * FROM media;"
