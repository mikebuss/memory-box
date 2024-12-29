#!/usr/bin/env python3

import json
import logging
from sqlite3 import IntegrityError
import sys
import sys
import psycopg2
import time
import subprocess
from flask import Flask, request, jsonify
import atexit
import signal
import random

sys.path.append("/home/mikebuss/epd/")
from download_image_update_display import download_image, process_image
from update_display import safe_update_display
from clear_display import clear_epd, sleep_epd
from utilities import *
import time
import serial
import adafruit_fingerprint
import os
import shutil
from werkzeug.utils import secure_filename

uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

random_image_update_frequency = 600  # seconds
fingerprint_fetch_frequency = 1  # seconds
app = Flask(__name__)
DATABASE_URL = "postgresql://postgres:HelloWorld12345@localhost/postgres"
is_exiting = False
is_in_night_mode = False
ignore_quiet_time = True

poll_fingerprints_thread = None
run_scheduled_items_thread = None
current_media_id = None

from threading import Thread
import schedule


def get_fingerprint():
    """Get a finger print image, template it, and see if it matches!"""
    logging.info("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    logging.info("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    logging.info("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True


def update_with_random_media():
    global current_media_id

    ensure_mount()

    try:
        logging.info(
            "Updating display with random media at %s",
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        )
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, black_image_path, red_image_path, description FROM media"
        )
        results = cur.fetchall()
        if len(results) == 1:
            logging.info("Only one media object to choose from, skipping update.")
            return
        while True:
            result = random.choice(results)
            if result[0] != current_media_id:
                break
        current_media_id = result[0]

        logging.info("Updating display with image: %s", result[3])
        safe_update_display(result[1], result[2])
        cur.close()
        conn.close()
    except Exception as e:
        logging.error("An error occurred in update_with_random_media: %s", e)


def process_received_image(
    tmp_black_image_path,
    tmp_red_image_path,
    payload,
    image_folder,
    downloaded_image_path,
):
    print("Payload object for debugging:", payload)

    # Get the image data
    image_url = payload["media"]["url"]
    date_taken = payload["media"]["date"]
    description = payload["media"]["description"]

    black_image_md5 = compute_md5(tmp_black_image_path)
    red_image_md5 = compute_md5(tmp_red_image_path)

    logging.debug(
        "Image data:\n- URL: %s\n- Date: %s\n- Description: %s\n- Processed image paths:\n\t- Black: %s\n\t- Red: %s\nImage MD5s:\n\t- Black: %s\n\t- Red: %s",
        image_url,
        date_taken,
        description,
        tmp_black_image_path,
        tmp_red_image_path,
        black_image_md5,
        red_image_md5,
    )

    # Store in the database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Check for duplicates
    cur.execute(
        "SELECT id FROM media WHERE black_image_md5 = %s OR red_image_md5 = %s",
        (black_image_md5, red_image_md5),
    )
    existing_media = cur.fetchone()
    if existing_media:
        logging.info("Media with given images already exists!")
        return jsonify({"message": "Media with given images already exists!"}), 409

    # Insert Media entry
    cur.execute(
        "INSERT INTO media (date_taken, description, image_url, black_image_md5, red_image_md5) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (
            date_taken,
            description,
            image_url,
            black_image_md5,
            red_image_md5,
        ),
    )
    media_id = cur.fetchone()[0]
    logging.info("Inserted media entry with ID: %s", media_id)

    # Move the images to a permanent location with the naming scheme ([ID]-[R or B].bmp)
    final_black_image_path = os.path.join(image_folder, f"{media_id}-B.bmp")
    final_red_image_path = os.path.join(image_folder, f"{media_id}-R.bmp")
    final_image_path = os.path.join(image_folder, f"{media_id}-O.bmp")
    shutil.move(tmp_black_image_path, final_black_image_path)
    shutil.move(tmp_red_image_path, final_red_image_path)
    shutil.move(downloaded_image_path, final_image_path)
    logging.debug(
        "Moved images to final paths: Black=%s, Red=%s, Original=%s",
        final_black_image_path,
        final_red_image_path,
        final_image_path,
    )

    # Update the database with the new image paths
    cur.execute(
        "UPDATE media SET black_image_path = %s, red_image_path = %s, image_path = %s WHERE id = %s",
        (final_black_image_path, final_red_image_path, final_image_path, media_id),
    )
    logging.info("Updated media entry with image paths for ID: %s", media_id)

    # Link Media with People
    if "people" in payload["media"]:
        for person_name in payload["media"]["people"]:
            try:
                cur.execute(
                    "INSERT INTO people (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                    (person_name,),
                )
                cur.execute("SELECT id FROM people WHERE name = %s", (person_name,))
                person_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO media_people (media_id, person_id) VALUES (%s, %s)",
                    (media_id, person_id),
                )
                logging.info(
                    "Linked media ID %s with person ID %s", media_id, person_id
                )
            except IntegrityError:
                conn.rollback()  # Rollback if there's a unique constraint error
                logging.error(
                    "Integrity error while linking media with person '%s'", person_name
                )
                return (
                    jsonify({"error": f"Person '{person_name}' already exists!"}),
                    400,
                )

    conn.commit()
    cur.close()
    conn.close()
    logging.info("Media stored successfully!")

    # Because the mobile app can upload several images at once,
    # don't update the display immediately for every image. Only if the metadata says to.

    # Update the display on a separate thread so we don't block the response.
    # Some clients will time out when the server takes too much time.
    if payload.get("update_display_immediately") == True:
        thread = Thread(
            target=update_display_with_images,
            args=(
                final_black_image_path,
                final_red_image_path,
            ),
        )
        thread.start()

    return jsonify({"message": "Media stored successfully!"}), 201


def update_with_specific_media(media_id):
    ensure_mount()

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, black_image_path, red_image_path, description FROM media WHERE id = %s",
            (media_id,),
        )
        result = cur.fetchone()
        if not result:
            logging.error("No media found for the given media ID.")
            cur.close()
            conn.close()
            return -1

        logging.info("Updating display with image: %s", result[3])
        safe_update_display(result[1], result[2])
        cur.close()
        conn.close()
        return media_id
    except Exception as e:
        logging.error("An error occurred in update_with_specific_media: %s", e)
        return -1


def update_with_fingerprint(finger_id):
    ensure_mount()

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # First, fetch the person_id for the given fingerprint_id
    cur.execute(
        "SELECT person_id FROM people_fingerprints WHERE fingerprint_id = %s",
        (finger_id,),
    )
    person = cur.fetchone()

    if not person:
        logging.info("No person found for the given fingerprint ID.")
        cur.close()
        conn.close()
        return

    person_id = person[0]

    # Now, fetch a random media for that person
    cur.execute(
        """
        SELECT description, black_image_path, red_image_path
        FROM media m
        INNER JOIN media_people mp ON m.id = mp.media_id
        WHERE mp.person_id = %s
        ORDER BY RANDOM() LIMIT 1
        """,
        (person_id,),
    )
    result = cur.fetchone()
    if result:
        logging.info("Fetched media: %s", result[0])
    else:
        logging.info("No media fetched.")

    if result:
        safe_update_display(result[1], result[2])
    else:
        logging.info(
            "No media found for the person corresponding to the given fingerprint ID."
        )

    cur.close()
    conn.close()

    time.sleep(2)


def set_led(color, mode, speed=255):
    global is_in_night_mode
    if is_in_night_mode:
        # Turn off the LED
        logging.debug("Night mode: keeping LED off")
        finger.set_led(color=color, mode=4, speed=speed)
        pass
    else:
        if color == 1:
            logging.debug("LED color is set to Red")
        elif color == 2:
            logging.debug("LED color is set to Blue")
        elif color == 3:
            logging.debug("LED color is set to Purple")
        finger.set_led(color=color, mode=mode, speed=speed)


def cleanup_and_exit(*args):
    global is_exiting
    """Function to cleanup resources on exit"""
    try:
        is_exiting = True
        set_led(color=0, mode=4)  # Turning off the LED
    except Exception as e:
        logging.error("An error occurred while turning off LED: %s", e)

    sys.exit(0)


def update_display_with_images(black_image_path, red_image_path):
    logging.info(
        "Updating display with most recent image. Time: %s",
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    )
    safe_update_display(black_image_path, red_image_path)


@app.route("/nightmode/on", methods=["GET"])
def turn_on_night_mode():
    global is_in_night_mode
    logging.info("Turning on night mode")
    is_in_night_mode = True
    set_led(color=1, mode=4)
    return jsonify({"message": "Night mode turned on"}), 200


@app.route("/nightmode/off", methods=["GET"])
def turn_off_night_mode():
    global is_in_night_mode
    logging.info("Turning off night mode")
    is_in_night_mode = False
    set_led(color=2, mode=1)
    return jsonify({"message": "Night mode turned off"}), 200


@app.route("/media/select", methods=["GET"])
def update_display_with_media_id():
    media_id = request.args.get("id")
    if media_id:
        logging.info("Updating display with media ID: %s", media_id)
        result = update_with_specific_media(media_id)
        if result == -1:
            return jsonify({"error": "No media found for the given media ID."}), 404
        else:
            return jsonify({"message": "Display updated successfully!"}), 200
    else:
        return jsonify({"error": "No media ID provided."}), 400


@app.route("/media", methods=["POST"])
def store_media():
    logging.info("Received POST request at /media")
    payload = request.json
    image_url = payload["media"]["url"]

    # Download and process the image
    download_folder = "/mnt/sda2/tmp"
    image_folder = "/mnt/sda2/images"

    downloaded_image_path = download_image(image_url, download_folder)
    logging.debug("Downloaded image path: %s", downloaded_image_path)
    tmp_black_image_path, tmp_red_image_path = process_image(
        downloaded_image_path, image_folder
    )

    return process_received_image(
        tmp_black_image_path,
        tmp_red_image_path,
        payload,
        image_folder,
        downloaded_image_path,
    )


@app.route("/media-direct-upload", methods=["POST"])
def upload_media():
    logging.info("Received POST request at /media-direct-upload")

    # Ensure both the file part and the metadata part exist in the request
    if "file" not in request.files or "metadata" not in request.form:
        return jsonify({"error": "Missing file or metadata"}), 400

    file = request.files["file"]
    metadata = request.form["metadata"]

    try:
        # Parse the JSON metadata
        metadata_json = json.loads(metadata)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON metadata"}), 400

    # Validate and process the image file
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        download_folder = "/mnt/sda2/tmp"
        image_folder = "/mnt/sda2/images"

        downloaded_image_path = os.path.join(download_folder, filename)
        file.save(downloaded_image_path)

        print("Downloaded image path: ", downloaded_image_path)

        # Process image similar to the original function
        tmp_black_image_path, tmp_red_image_path = process_image(
            downloaded_image_path, image_folder
        )

        return process_received_image(
            tmp_black_image_path,
            tmp_red_image_path,
            metadata_json,
            image_folder,
            downloaded_image_path,
        )
    else:
        return jsonify({"error": "Invalid file type"}), 400


def allowed_file(filename):
    # Check for allowed file extensions
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def periodically_scan_fingerprint():
    global is_exiting, poll_fingerprints_thread, run_scheduled_items_thread
    while is_exiting == False:
        try:
            current_time = time.localtime()
            if (
                current_time.tm_hour >= 19 or current_time.tm_hour < 9
            ) and ignore_quiet_time == False:
                logging.info(
                    "We're in the quiet time. Current time is %s",
                    time.strftime("%H:%M:%S", current_time),
                )
                set_led(color=1, mode=4)  # Turn off the LED during the downtime
                time.sleep(3600)  # Sleep for an hour
                continue

            set_led(color=2, mode=1, speed=255)

            if get_fingerprint():
                logging.info(
                    "Detected # %s with confidence %s",
                    finger.finger_id,
                    finger.confidence,
                )
                set_led(color=3, mode=3)
                update_with_fingerprint(finger.finger_id)
                time.sleep(2)
            else:
                logging.info("Finger not found")
                set_led(color=1, mode=3)
                time.sleep(2)

            time.sleep(fingerprint_fetch_frequency)
        except Exception as e:
            logging.error("An error occurred while scanning for fingerprints: %s", e)
            time.sleep(1)
    logging.info("Exiting fingerprint polling thread.")


def run_scheduled_items():
    while is_exiting == False:
        schedule.run_pending()
        time.sleep(1)


def run_clear_epd_script():
    script_to_run = "/home/mikebuss/epd/clear_display.py"
    subprocess.run(["sudo", "python", script_to_run], check=True)


if __name__ == "__main__":
    atexit.register(cleanup_and_exit)
    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)

    # Setup logging
    logging.basicConfig(filename="/mnt/sda2/logs/memorybox.log", level=logging.INFO)
    logging.info("MemoryBox script started.")

    try:
        subprocess.run(["sudo", "systemctl", "restart", "postgresql"], check=True)
        logging.info("Successfully restarted PostgreSQL.")
    except subprocess.CalledProcessError as e:
        logging.error("Failed to restart PostgreSQL. Error: %s", e)

    ensure_mount()

    # Rest of your script starts here.
    logging.info("Checks passed. Running...")

    # Schedule tasks
    for minute in range(0, 60, 30):
        minute_str = str(minute).zfill(2)  # Ensure minute is always two digits
        for hour in range(6, 22):
            hour_str = str(hour).zfill(2)  # Ensure hour is always two digits
            logging.info("Scheduling for time: %s:%s", hour_str, minute_str)
            schedule.every().day.at(f"{hour_str}:{minute_str}").do(
                update_with_random_media
            )

    # 21:35 is 9:35 PM. Clear the display then, when everyone goes to bed.
    schedule.every().day.at(f"21:35").do(run_clear_epd_script)

    poll_fingerprints_thread = Thread(target=periodically_scan_fingerprint)
    poll_fingerprints_thread.daemon = True
    poll_fingerprints_thread.start()

    run_scheduled_items_thread = Thread(target=run_scheduled_items)
    run_scheduled_items_thread.daemon = True
    run_scheduled_items_thread.start()

    app.run(host="0.0.0.0", port=2358)
