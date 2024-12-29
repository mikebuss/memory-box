#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import time
from PIL import Image
import logging
from threading import Lock

display_update_lock = Lock()


sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib"))

try:
    from waveshare_epd import epd7in5b_V2
except ImportError:
    logging.error("Please install waveshare_epd package to proceed.")
    sys.exit(1)

logging.basicConfig(level=logging.DEBUG)

TIME_LIMIT = 180  # Time limit in seconds
LAST_UPDATE_FILE = "/home/mikebuss/services/memorybox/last_update_time.txt"


def safe_update_display(black_image_path, red_image_path):
    with display_update_lock:
        update_display(black_image_path, red_image_path)


def update_display(bw_path, red_path):
    logging.info("Starting EPD update process.")

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

        # Create the file and set the last update time to the current time minus TIME_LIMIT
        with open(LAST_UPDATE_FILE, "w") as f:
            last_update_time = time.time() - TIME_LIMIT
            f.write(str(last_update_time))

    try:
        # Initialize EPD
        logging.info("Initializing the EPD.")
        epd = epd7in5b_V2.EPD()
        epd.init()
        epd.Clear()

        # Check if files exist
        if os.path.exists(bw_path) and os.path.exists(red_path):
            logging.info("Both image files exist.")
        else:
            logging.error("One or both image files do not exist.")
            return False, "One or both image files do not exist."

        # Load Images
        logging.info("Loading image files.")
        Himage_bw = Image.open(bw_path)
        Himage_red = Image.open(red_path)

        # Check image resolutions
        if Himage_bw.size == (800, 480) and Himage_red.size == (800, 480):
            logging.info("Image resolutions are correct.")
        else:
            logging.error("Image resolution must be 800x480.")
            return False, "Image resolution must be 800x480."

        # Update EPD
        logging.info("Updating the EPD.")
        epd.display(epd.getbuffer(Himage_bw), epd.getbuffer(Himage_red))

        # Sleep
        logging.info("Putting EPD to sleep.")
        epd.sleep()

        # Update last update time
        logging.info("Updating the last update time.")
        with open(LAST_UPDATE_FILE, "w") as f:
            f.write(str(time.time()))

        logging.info("EPD update process completed successfully.")
        return True, "Successfully updated EPD."

    except Exception as e:
        logging.error("An exception occurred: {}".format(e))
        epd7in5b_V2.epdconfig.module_exit()
        return False, str(e)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        logging.error(
            "Usage: python epd_update.py [black/white image path] [red image path]"
        )
        sys.exit(1)

    success, message = update_display(sys.argv[1], sys.argv[2])
    if success:
        logging.info(f"Success: {message}")
    else:
        logging.error(f"Error: {message}")
