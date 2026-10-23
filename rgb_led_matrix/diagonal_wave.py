"""Diagonal sine wave moving towards the bottom-right corner.

Each pixel gets intensity sin(2*pi*((x + y) / 126 - t / 64)), mapped to 0..255.
Run on the Pi Zero 2W: sudo ~/rgbmatrix/.venv/bin/python rgb_led_matrix/diagonal_wave.py
"""

import math
import time

from matrix_config import COLS, ROWS, create_matrix

# t goes 0..63; dividing by 64 (not 63) lets frame 63 flow into frame 0 without
# showing the same picture twice.
FRAMES = 64
FPS = 30
COLOR = (255, 255, 255)  # white; the intensity scales each channel

Pixel = tuple[int, int, int]


def build_frames() -> list[list[Pixel]]:
    """Return, for each t, the colour for every diagonal index d = x + y.

    Intensity only depends on x + y, so 127 values per frame are enough
    instead of 4096; this keeps the per-frame work on the Zero small.
    """
    max_d = (COLS - 1) + (ROWS - 1)  # 126
    frames = []
    for t in range(FRAMES):
        row = []
        for d in range(max_d + 1):
            # Minus t moves the crests towards larger x + y, i.e. right and down.
            s = math.sin(2 * math.pi * (d / max_d - t / FRAMES))
            level = (s + 1) / 2  # sin is -1..1, LEDs need 0..1
            r, g, b = COLOR
            row.append((round(r * level), round(g * level), round(b * level)))
        frames.append(row)
    return frames


def main() -> None:
    frames = build_frames()
    matrix = create_matrix()
    canvas = matrix.CreateFrameCanvas()
    try:
        while True:
            for colors in frames:
                start = time.monotonic()
                for y in range(ROWS):
                    for x in range(COLS):
                        canvas.SetPixel(x, y, *colors[x + y])
                # Draw off-screen, then swap, so a half-drawn frame is never shown.
                canvas = matrix.SwapOnVSync(canvas)
                time.sleep(max(0.0, 1 / FPS - (time.monotonic() - start)))
    except KeyboardInterrupt:
        pass
    finally:
        matrix.Clear()


if __name__ == "__main__":
    main()
