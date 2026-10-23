"""Turn any image into a 64x64 RGB PNG for the panel (runs on the host).

The image is centre-cropped to a square first, so it is never stretched.
Colours keep their full 8 bits per channel; no bit reduction here.

Usage (host): uv run object_files/resize_to_64x64.py source_files/images/taylor_swift.png
Output: object_files/images/<name>_64x64bits.png
"""

import argparse
from pathlib import Path

from PIL import Image

SIZE = 64
SUFFIX = "_64x64bits"
OUTPUT_DIR = Path(__file__).resolve().parent / "images"


def crop_center_square(img: Image.Image) -> Image.Image:
    """Cut the longer side down to the shorter one, keeping the middle."""
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def to_rgb_on_black(img: Image.Image) -> Image.Image:
    """Drop transparency by putting the image on black, i.e. LEDs off."""
    img = img.convert("RGBA")
    background = Image.new("RGBA", img.size, (0, 0, 0, 255))
    return Image.alpha_composite(background, img).convert("RGB")


def resize_to_64x64(input_path: Path) -> Path:
    with Image.open(input_path) as img:
        square = crop_center_square(to_rgb_on_black(img))
    # LANCZOS keeps the most detail when shrinking a lot (e.g. 855 -> 64).
    small = square.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{input_path.stem}{SUFFIX}.png"
    small.save(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("image", type=Path, help="path to the source image")
    args = parser.parse_args()
    print(f"Saved {resize_to_64x64(args.image)}")


if __name__ == "__main__":
    main()
