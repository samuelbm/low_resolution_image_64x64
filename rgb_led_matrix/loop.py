"""Show every 64x64 image and GIF of a folder in turn, in a loop, until Ctrl+C.

Each GIF plays a set number of times, a still image stays a set number of
seconds, then the next file comes.
Run on the Pi Zero 2W, from the repo root:
  sudo ~/rgbmatrix/.venv/bin/python rgb_led_matrix/loop.py object_files/gifs
"""

import argparse
import time
from pathlib import Path

from matrix_config import create_matrix
from PIL import Image
from rgbmatrix import FrameCanvas, RGBMatrix
from show_gif import load_gif
from show_image import load_image

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp"}
GIF_SUFFIX = ".gif"
DEFAULT_PLAYS = 2
DEFAULT_IMAGE_SECONDS = 10.0

# Each frame with how long to show it (s); a still image is one frame.
Frames = list[tuple[Image.Image, float]]


def positive_int(text: str) -> int:
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be more than 0")
    return value


def positive_float(text: str) -> float:
    value = float(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be more than 0")
    return value


def load_folder(folder: Path) -> list[tuple[str, Frames]]:
    """Load every image and GIF of the folder, sorted by name.

    Everything is loaded here, before the matrix is created: the library then
    drops root, and the files in the home folder may no longer be readable.
    """
    items = []
    for path in sorted(folder.iterdir()):
        suffix = path.suffix.lower()
        if path.name.startswith(".") or not path.is_file():
            continue
        try:
            if suffix == GIF_SUFFIX:
                frames = load_gif(path)
            elif suffix in IMAGE_SUFFIXES:
                frames = [(load_image(path), 0.0)]
            else:
                continue
        except (ValueError, OSError) as error:
            # One bad file should not stop the rest of the show.
            print(f"skipped {path.name}: {error}")
            continue
        items.append((path.name, frames))
    return items


def play_item(
    matrix: RGBMatrix,
    pool: list[FrameCanvas],
    shown: int,
    frames: Frames,
    plays: int,
    image_seconds: float,
) -> int:
    """Play a GIF `plays` times, or show a still image for `image_seconds`.

    Returns the index of the canvas left on screen.

    Canvases are reused from `pool`: the library never frees a canvas, so
    creating new ones for every item would leak memory over a long run.
    """
    while len(pool) < len(frames) + 1:
        pool.append(matrix.CreateFrameCanvas())
    # Skip the canvas on screen, so the previous item stays intact until the
    # first swap instead of being overwritten while visible.
    indexes = [i for i in range(len(pool)) if i != shown][: len(frames)]
    for i, (image, _) in zip(indexes, frames):
        pool[i].SetImage(image)

    # A one-frame GIF has nothing to animate: treat it like a still image.
    if len(frames) == 1:
        matrix.SwapOnVSync(pool[indexes[0]])
        time.sleep(image_seconds)
        return indexes[0]

    # Each frame is due at a fixed time after the previous one, so small
    # delays do not add up and the GIF keeps its speed.
    due = time.monotonic()
    for _ in range(plays):
        for i, (_, duration) in zip(indexes, frames):
            matrix.SwapOnVSync(pool[i])
            shown = i
            due += duration
            time.sleep(max(0.0, due - time.monotonic()))
    return shown


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Show every 64x64 image and GIF of a folder in turn: each GIF "
            "plays a few times, each still image stays a few seconds, then the "
            "next file comes. After the last file it starts again from the "
            "first one. Stop with Ctrl+C."
        ),
        epilog=(
            "example: sudo ~/rgbmatrix/.venv/bin/python rgb_led_matrix/loop.py "
            "object_files/gifs/halloween --plays 3"
        ),
    )
    parser.add_argument(
        "folder_path",
        type=Path,
        help=(
            "folder holding the files to show (.png, .jpg, .jpeg, .bmp, .gif), "
            "played in name order; sub-folders and other files are ignored. "
            "Files must be 64x64 (made with the cutter); others are skipped."
        ),
    )
    parser.add_argument(
        "--plays",
        type=positive_int,
        default=DEFAULT_PLAYS,
        help=f"how many times each GIF plays in a row (default {DEFAULT_PLAYS})",
    )
    parser.add_argument(
        "--image-seconds",
        type=positive_float,
        default=DEFAULT_IMAGE_SECONDS,
        help=(
            "how long each still image stays, in seconds; decimals allowed "
            f"(default {DEFAULT_IMAGE_SECONDS:g})"
        ),
    )
    args = parser.parse_args()

    if not args.folder_path.is_dir():
        raise SystemExit(f"{args.folder_path} is not a folder")
    items = load_folder(args.folder_path)
    if not items:
        raise SystemExit(f"nothing to show in {args.folder_path}")
    print(f"{len(items)} files: GIFs {args.plays}x, images {args.image_seconds:g} s")

    matrix = create_matrix()
    pool: list[FrameCanvas] = []
    shown = -1
    try:
        while True:
            for name, frames in items:
                print(f"showing {name}")
                shown = play_item(
                    matrix, pool, shown, frames, args.plays, args.image_seconds
                )
    except KeyboardInterrupt:
        pass
    finally:
        matrix.Clear()


if __name__ == "__main__":
    main()
