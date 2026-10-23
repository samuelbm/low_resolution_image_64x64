"""Same diagonal wave as diagonal_wave.py, with the panel driven at 4 PWM bits.

Fewer bits allow much longer pulses at a high refresh rate, which hides the
timing jitter of the Bonnet without the GPIO4-GPIO18 mod. Cost: 16 levels
per colour, so the wave shows visible steps.
Run on the Pi Zero 2W: sudo ~/rgbmatrix/.venv/bin/python rgb_led_matrix/diagonal_wave_4bits.py
"""

from matrix_config import LOW_BIT_PWM_BITS, LOW_BIT_PWM_LSB_NANOSECONDS, create_matrix
from utils import build_wave_frames, run_wave


def main() -> None:
    frames = build_wave_frames()
    matrix = create_matrix(
        pwm_bits=LOW_BIT_PWM_BITS,
        pwm_lsb_nanoseconds=LOW_BIT_PWM_LSB_NANOSECONDS,
    )
    run_wave(matrix, frames)


if __name__ == "__main__":
    main()
