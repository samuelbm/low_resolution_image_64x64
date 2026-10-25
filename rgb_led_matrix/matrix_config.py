"""Single place for the matrix settings (CLAUDE.md §5)."""

from rgbmatrix import RGBMatrix, RGBMatrixOptions

ROWS = 64
COLS = 64
# The GPIO4-GPIO18 wire is soldered (D-010): OE pulses come from the Pi's PWM
# hardware. Never go back to "adafruit-hat" while the wire is on.
HARDWARE_MAPPING = "adafruit-hat-pwm"
# Value that worked at first light (Iteration 1).
GPIO_SLOWDOWN = 2
BRIGHTNESS = 50  # percent

# Library defaults: smooth colours, but dim colours shimmer on the Bonnet.
PWM_BITS = 11
PWM_LSB_NANOSECONDS = 130

# Low-bit profile: 16 levels per colour, long pulses to hide the timing jitter
# and the ghosting, still a high refresh rate. Values to tune on the panel.
LOW_BIT_PWM_BITS = 4
LOW_BIT_PWM_LSB_NANOSECONDS = 1000


def create_matrix(
    pwm_bits: int = PWM_BITS,
    pwm_lsb_nanoseconds: int = PWM_LSB_NANOSECONDS,
) -> RGBMatrix:
    options = RGBMatrixOptions()
    options.rows = ROWS
    options.cols = COLS
    options.hardware_mapping = HARDWARE_MAPPING
    options.gpio_slowdown = GPIO_SLOWDOWN
    options.brightness = BRIGHTNESS
    options.pwm_bits = pwm_bits
    options.pwm_lsb_nanoseconds = pwm_lsb_nanoseconds
    # Prints the refresh rate in the terminal, to compare the two profiles.
    options.show_refresh_rate = 1
    return RGBMatrix(options=options)
