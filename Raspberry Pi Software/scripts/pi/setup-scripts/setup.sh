#!/bin/bash
ALL_START_TIME=$SECONDS

# List of scripts to run
scripts=("setup-system.sh" "setup-ssd.sh" "setup-pql.sh" "setup-waveshare.sh")

# Execute each script
for script in "${scripts[@]}"; do
  if [[ -x "$script" ]]; then  # Check if the script is executable
    ./$script
    # If script fails, exit with an error
    if [[ $? -ne 0 ]]; then
      echo "Script $script failed. Exiting."
      exit 1
    fi
  else
    echo "Script $script is not executable or does not exist. Exiting."
    exit 1
  fi
done

ELAPSED_TIME=$(($SECONDS - $ALL_START_TIME))
echo "Elapsed time: $ELAPSED_TIME seconds"
