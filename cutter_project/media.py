"""Loading images and GIFs for the cutter, without any GUI code."""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageSequence
from resize_to_64x64 import SIZE, to_rgb_on_black

# Browsers show GIF frames with a delay under 20 ms (often written as 0) at
# 100 ms; doing the same keeps such GIFs at the speed people know them by.
MIN_FRAME_MS = 20
DEFAULT_FRAME_MS = 100

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
GIF_SUFFIXES = {".gif"}

Square = tuple[int, int, int]  # left, top, side, in source pixels

# Smallest square the user can make: below this the result is mostly blur.
MIN_SIDE = 8
# For each corner: which way it points (x, y). The opposite corner stays put.
CORNER_DIRECTIONS = {"nw": (-1, -1), "ne": (1, -1), "sw": (-1, 1), "se": (1, 1)}


@dataclass
class Media:
    path: Path
    frames: list[Image.Image]  # RGBA, full source size
    durations_ms: list[int]  # one per frame

    @property
    def size(self) -> tuple[int, int]:
        return self.frames[0].size

    @property
    def is_animated(self) -> bool:
        return len(self.frames) > 1


def list_files(folder: Path, suffixes: set[str]) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(
        (p for p in folder.iterdir() if p.suffix.lower() in suffixes),
        key=lambda p: p.name.lower(),
    )


def load_media(path: Path) -> Media:
    frames = []
    durations = []
    with Image.open(path) as img:
        # Pillow hands out each GIF frame already composed over the previous
        # ones, so every frame is a complete picture.
        for frame in ImageSequence.Iterator(img):
            frames.append(frame.convert("RGBA"))
            duration = frame.info.get("duration", DEFAULT_FRAME_MS)
            durations.append(DEFAULT_FRAME_MS if duration < MIN_FRAME_MS else duration)
    return Media(path, frames, durations)


def fit_size(size: tuple[int, int], box: tuple[int, int]) -> tuple[int, int]:
    """Largest size with the same ratio as `size` that fits inside `box`."""
    w, h = size
    scale = min(box[0] / w, box[1] / h)
    return max(1, round(w * scale)), max(1, round(h * scale))


def centered_square(size: tuple[int, int], side: int = SIZE) -> Square:
    """Square of `side` source pixels in the middle, shrunk if the image is smaller."""
    w, h = size
    side = min(side, w, h)
    return (w - side) // 2, (h - side) // 2, side


def crop_result(frame: Image.Image, square: Square) -> Image.Image:
    """What the panel gets: the square, on black, scaled to 64x64 RGB."""
    left, top, side = square
    crop = frame.crop((left, top, left + side, top + side))
    # Same steps and filter as resize_to_64x64.py, so preview and saved file
    # match. A 64-pixel square is passed through unchanged.
    return to_rgb_on_black(crop).resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def move_square(square: Square, left: int, top: int, size: tuple[int, int]) -> Square:
    """Square moved to (left, top), pushed back inside the image if needed."""
    side = square[2]
    w, h = size
    return min(max(0, left), w - side), min(max(0, top), h - side), side


def resize_square(
    square: Square,
    corner: str,
    x: float,
    y: float,
    size: tuple[int, int],
    min_side: int = MIN_SIDE,
) -> Square:
    """Square with `corner` dragged to source point (x, y).

    The opposite corner is the anchor and does not move. The side follows
    whichever of x or y is further out, so the square stays a square and the
    dragged corner is never behind the mouse.
    """
    left, top, side = square
    w, h = size
    dx, dy = CORNER_DIRECTIONS[corner]
    anchor_x = left + side if dx < 0 else left
    anchor_y = top + side if dy < 0 else top
    # Room between the anchor and the image border, towards the dragged corner.
    room_x = anchor_x if dx < 0 else w - anchor_x
    room_y = anchor_y if dy < 0 else h - anchor_y
    max_side = min(room_x, room_y)
    wanted = max((x - anchor_x) * dx, (y - anchor_y) * dy)
    new_side = round(min(max(wanted, min(min_side, max_side)), max_side))
    new_left = anchor_x - new_side if dx < 0 else anchor_x
    new_top = anchor_y - new_side if dy < 0 else anchor_y
    return new_left, new_top, new_side
