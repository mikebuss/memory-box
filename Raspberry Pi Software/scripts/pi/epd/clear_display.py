#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import time  # Required for sleep
from PIL import Image
import logging

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib"))

try:
    from waveshare_epd import epd7in5b_V2
except ImportError:
    logging.error("Please install waveshare_epd package to proceed.")
    sys.exit(1)

logging.basicConfig(level=logging.DEBUG)

TIME_LIMIT = 180  # Time limit in seconds
LAST_UPDATE_FILE = "last_update_time.txt"


def sleep_epd():
    logging.info("Putting EPD to sleep in sleep_epd() function.")
    epd = epd7in5b_V2.EPD()
    epd.init()
    epd.Clear()


def clear_epd():
    logging.info("Starting EPD clearing process.")

    # Check if the last update file exists
    if os.path.exists(LAST_UPDATE_FILE):
        logging.info(f"The last update file '{LAST_UPDATE_FILE}' exists.")
        with open(LAST_UPDATE_FILE, "r") as f:
            last_update_time = float(f.read().strip())
        elapsed_time = time.time() - last_update_time
        logging.info(f"{elapsed_time:.2f} seconds have elapsed since the last update.")

        if elapsed_time < TIME_LIMIT:
            wait_time = TIME_LIMIT - elapsed_time
            logging.info(f"Need to wait for an additional {int(wait_time)} seconds.")
            for remaining in range(int(wait_time), 0, -1):
                sys.stdout.write(f"\r{remaining} seconds remaining.")
                sys.stdout.flush()
                time.sleep(1)
            print()

    else:
        logging.info(f"The last update file '{LAST_UPDATE_FILE}' does not exist.")

    try:
        # Initialize EPD
        logging.info("Initializing the EPD.")
        epd = epd7in5b_V2.EPD()
        epd.init()
        epd.Clear()

        # Sleep
        logging.info("Putting EPD to sleep.")
        epd.sleep()

        # Update last update time
        logging.info("Updating the last update time.")
        with open(LAST_UPDATE_FILE, "w") as f:
            f.write(str(time.time()))

        logging.info("EPD cleared successfully.")
        return True, "Successfully cleared EPD."

    except Exception as e:
        logging.error("An exception occurred: {}".format(e))
        epd7in5b_V2.epdconfig.module_exit()
        return False, str(e)


if __name__ == "__main__":
    success, message = clear_epd()
    if success:
        logging.info(f"Success: {message}")
    else:
        logging.error(f"Error: {message}")
