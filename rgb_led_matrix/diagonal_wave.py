"""Diagonal sine wave moving towards the bottom-right corner.

Each pixel gets intensity sin(2*pi*((x + y) / 126 - t / 64)), mapped to 0..255.
Run on the Pi Zero 2W: sudo ~/rgbmatrix/.venv/bin/python rgb_led_matrix/diagonal_wave.py
"""

from matrix_config import create_matrix
from utils import build_wave_frames, run_wave


def main() -> None:
    frames = build_wave_frames()
    run_wave(create_matrix(), frames)


if __name__ == "__main__":
    main()
