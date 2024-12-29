import os
import sys
import hashlib
import subprocess

device = "/dev/sda2"
mount_point = "/mnt/sda2"


def is_mounted(mount_point):
    return os.path.ismount(mount_point)


def mount_device(device, mount_point):
    subprocess.run(
        [
            "sudo",
            "mount",
            "-t",
            "ext4",
            "UUID=19d4a257-01a1-4646-9bef-a3e868980368",
            "/mnt/sda2",
        ]
    )


def ensure_mount():
    global device, mount_mount

    if not is_mounted(mount_point):
        print(f"{mount_point} is not mounted. Attempting to mount...")
        try:
            mount_device(device, mount_point)
            print(f"Mounted {device} at {mount_point}")
        except Exception as e:
            print(f"Failed to mount {device} at {mount_point}")
            sys.exit(1)
    else:
        print(f"{mount_point} is already mounted.")


def compute_md5(file_path):
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()
