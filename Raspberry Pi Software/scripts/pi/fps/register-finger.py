import psycopg2
import time
import adafruit_fingerprint
import serial

DATABASE_URL = "postgresql://postgres:HelloWorld12345@localhost/postgres"
uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)


def enroll_finger(location):
    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="")
        else:
            print("Place same finger again...", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                return False
            else:
                print("Other error")
                return False

        print("Templating...", end="")
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
            else:
                print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print("Storing model #%d..." % location, end="")
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        print("Stored")
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            print("Flash storage error")
        else:
            print("Other error")
        return False

    return True


def register_fingerprint():
    # Connect to the database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Ask for user inputs
    full_name = input("Enter the full name (first and last combined) of the person: ")
    while True:
        try:
            finger_id = int(input("Enter a unique integer ID for the fingerprint: "))
            break
        except ValueError:
            print("Please enter a valid integer.")

    # Check if the fingerprint ID already exists
    print("Check if the fingerprint ID already exists")
    cur.execute("SELECT * FROM fingerprints WHERE id = %s", (finger_id,))
    if cur.fetchone():
        print("The fingerprint ID already exists. Please use a different ID.")
        return

    finger.set_led(color=3, mode=1, speed=255)

    # Enroll the fingerprint
    if not enroll_finger(finger_id):
        print("Failed to enroll fingerprint. Aborting.")
        return

    # Check if the person already exists in the database
    print("Check if the person already exists in the database")
    cur.execute("SELECT id FROM people WHERE name = %s", (full_name,))
    person_record = cur.fetchone()

    if person_record:
        # Person exists, use their existing ID
        person_id = person_record[0]
    else:
        # Insert new person and get their ID
        print("Insert new person and get their ID")
        cur.execute("INSERT INTO people (name) VALUES (%s) RETURNING id", (full_name,))
        person_record = cur.fetchone()
        if person_record:
            person_id = person_record[0]
        else:
            print("Failed to insert the new person into the database.")
            return

    # Add the new fingerprint to the database
    print("Add the new fingerprint to the database")
    cur.execute("INSERT INTO fingerprints (id) VALUES (%s)", (finger_id,))

    # Link the fingerprint with the person
    print("Link the fingerprint with the person")
    cur.execute(
        "INSERT INTO people_fingerprints (person_id, fingerprint_id) VALUES (%s, %s)",
        (person_id, finger_id),
    )

    # Commit changes and close connection
    conn.commit()
    cur.close()
    conn.close()

    finger.set_led(color=1, mode=4)
    print(f"Fingerprint registered successfully for {full_name} with ID {finger_id}.")


# Run the script
register_fingerprint()
