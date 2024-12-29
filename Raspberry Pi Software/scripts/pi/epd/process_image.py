import sys
import io
import os
import traceback
from wand.image import Image as WandImage
from wand.color import Color
from PIL import Image

IMAGE_WIDTH = 800
IMAGE_HEIGHT = 480


def process_image(filename, output_folder, custom_filename=None):
    print(f"Processing file: {filename}")

    red_image = None
    black_image = None
    try:
        with WandImage(filename=filename) as img:
            img.resize(IMAGE_WIDTH, IMAGE_HEIGHT)

            with WandImage() as palette1:
                with WandImage(width=1, height=1, pseudo="xc:red") as red:
                    palette1.sequence.append(red)
                with WandImage(width=1, height=1, pseudo="xc:black") as black:
                    palette1.sequence.append(black)
                with WandImage(width=1, height=1, pseudo="xc:white") as white:
                    palette1.sequence.append(white)
                palette1.concat()

                img.remap(affinity=palette1, method="floyd_steinberg")

                red = img.clone()
                black = img.clone()

                red.opaque_paint(target="black", fill="white")
                black.opaque_paint(target="red", fill="white")

                red_image = Image.open(io.BytesIO(red.make_blob("bmp")))
                black_image = Image.open(io.BytesIO(black.make_blob("bmp")))

                red_image = red_image.convert("1")
                black_image = black_image.convert("1")

                base_filename = (
                    custom_filename
                    if custom_filename
                    else os.path.splitext(os.path.basename(filename))[0]
                )
                os.makedirs(output_folder, exist_ok=True)
                black_output_path = os.path.join(
                    output_folder, f"{base_filename}-black.bmp"
                )
                red_output_path = os.path.join(
                    output_folder, f"{base_filename}-red.bmp"
                )

                print(f"Saving black image to {black_output_path}")
                print(f"Saving red image to {red_output_path}")

                black_image.save(black_output_path)
                red_image.save(red_output_path)

                return black_output_path, red_output_path

    except Exception as ex:
        print(f"traceback.format_exc():\n{traceback.format_exc()}")
        return None


if __name__ == "__main__":
    print("Running...")

    file_path = sys.argv[1] if len(sys.argv) > 1 else "sample.jpeg"
    output_folder = sys.argv[2] if len(sys.argv) > 2 else "output"
    custom_filename = sys.argv[3] if len(sys.argv) > 3 else None

    red_image, black_image = process_image(file_path, output_folder, custom_filename)

    if red_image is None or black_image is None:
        print("Error processing image")
        sys.exit(1)
