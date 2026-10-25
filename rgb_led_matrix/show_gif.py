"""Play a 64x64 GIF on the panel, in a loop, until Ctrl+C.

Make the GIF on the host with the cutter (cutter_project/cutter_app.py).
Run on the Pi Zero 2W:
  sudo ~/rgbmatrix/.venv/bin/python rgb_led_matrix/show_gif.py <animation.gif>
"""

import argparse
import time
from pathlib import Path

from matrix_config import COLS, ROWS, create_matrix
from PIL import Image, ImageSequence

# Same rule as the cutter preview (cutter_project/media.py): browsers play
# frames with a delay under 20 ms (often written as 0) at 100 ms.
MIN_FRAME_MS = 20
DEFAULT_FRAME_MS = 100


def load_gif(path: Path) -> list[tuple[Image.Image, float]]:
    """Every frame as a complete RGB picture, with how long to show it (s)."""
    frames = []
    with Image.open(path) as gif:
        if gif.size != (COLS, ROWS):
            # Refuse instead of resizing: the Zero only displays, and a silent
            # resize would hide that the wrong file was passed.
            raise SystemExit(
                f"{path} is {gif.size[0]}x{gif.size[1]}, expected {COLS}x{ROWS}"
            )
        for frame in ImageSequence.Iterator(gif):
            duration = frame.info.get("duration", DEFAULT_FRAME_MS)
            if duration < MIN_FRAME_MS:
                duration = DEFAULT_FRAME_MS
            frames.append((frame.convert("RGB"), duration / 1000))
    return frames


def main() -> None:
    parser = argparse.ArgumentParser(description="Play a 64x64 GIF on the matrix.")
    parser.add_argument("gif", type=Path, help="path to a 64x64 GIF")
    args = parser.parse_args()

    frames = load_gif(args.gif)
    matrix = create_matrix()
    # Convert every frame into its own canvas once, up front. In the loop the
    # library then only switches canvases: no per-frame pixel work competes
    # with the panel refresh (the cause of the glitches on the moving wave).
    canvases = []
    for image, _ in frames:
        canvas = matrix.CreateFrameCanvas()
        canvas.SetImage(image)
        canvases.append(canvas)
    durations = [duration for _, duration in frames]

    try:
        # Each frame is due at a fixed time after the previous one, so small
        # delays do not add up and the GIF keeps its speed.
        due = time.monotonic()
        while True:
            for canvas, duration in zip(canvases, durations):
                matrix.SwapOnVSync(canvas)
                due += duration
                time.sleep(max(0.0, due - time.monotonic()))
    except KeyboardInterrupt:
        pass
    finally:
        matrix.Clear()


if __name__ == "__main__":
    main()
