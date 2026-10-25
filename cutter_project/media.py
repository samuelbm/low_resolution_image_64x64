"""Loading images and GIFs for the cutter, without any GUI code."""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageSequence

# Browsers show GIF frames with a delay under 20 ms (often written as 0) at
# 100 ms; doing the same keeps such GIFs at the speed people know them by.
MIN_FRAME_MS = 20
DEFAULT_FRAME_MS = 100

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
GIF_SUFFIXES = {".gif"}


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
