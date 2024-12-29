import sys
import os
import urllib.request
from process_image import process_image
from update_display import update_display


def download_image(url, download_folder):
    local_filename = os.path.join(download_folder, "temp_downloaded_image.jpg")
    urllib.request.urlretrieve(url, local_filename)
    return local_filename


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python main_script.py <image_url> [custom_filename]")
        sys.exit(1)

    image_url = sys.argv[1]
    custom_filename = sys.argv[2] if len(sys.argv) == 3 else None
    download_folder = "/mnt/sda2/tmp"
    image_folder = "/mnt/sda2/images"

    downloaded_image_path = None

    try:
        downloaded_image_path = download_image(image_url, download_folder)
        print(f"Downloaded image to {downloaded_image_path}")

        # Process the image
        black_image_path, red_image_path = process_image(
            downloaded_image_path, image_folder, custom_filename
        )

        if not black_image_path or not red_image_path:
            raise Exception("Image processing failed.")

        # Print both paths
        print(f"Black image path: {black_image_path}")
        print(f"Red image path: {red_image_path}")

        # Update the EPD
        update_display(black_image_path, red_image_path)
        print("Updated the ePaper display.")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    finally:
        if downloaded_image_path and os.path.exists(downloaded_image_path):
            os.remove(downloaded_image_path)
            print(f"Deleted temporary image at {downloaded_image_path}")


if __name__ == "__main__":
    main()
