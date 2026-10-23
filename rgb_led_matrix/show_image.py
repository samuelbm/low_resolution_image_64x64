"""Show one 64x64 image on the panel, without animation, until Ctrl+C.

Make the image on the host with object_files/resize_to_64x64.py.
Run on the Pi Zero 2W:
  sudo ~/rgbmatrix/.venv/bin/python rgb_led_matrix/show_image.py <image.png>
"""

import argparse
import time
from pathlib import Path

from matrix_config import COLS, ROWS, create_matrix
from PIL import Image


def load_image(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    # Refuse instead of resizing here: the Zero should only display, and a
    # silent resize would hide that the wrong file was passed.
    if img.size != (COLS, ROWS):
        raise SystemExit(
            f"{path} is {img.size[0]}x{img.size[1]}, expected {COLS}x{ROWS}"
        )
    return img


def main() -> None:
    parser = argparse.ArgumentParser(description="Show a 64x64 image on the matrix.")
    parser.add_argument("image", type=Path, help="path to a 64x64 image")
    args = parser.parse_args()

    img = load_image(args.image)
    matrix = create_matrix()
    try:
        matrix.SetImage(img)
        # The library keeps refreshing the panel in its own thread; we only wait.
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        matrix.Clear()


if __name__ == "__main__":
    main()
