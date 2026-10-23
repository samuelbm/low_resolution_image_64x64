"""Single place for the matrix settings (CLAUDE.md §5)."""

from rgbmatrix import RGBMatrix, RGBMatrixOptions

ROWS = 64
COLS = 64
# Use "adafruit-hat-pwm" only once the GPIO4-GPIO18 solder mod is done (D-004).
HARDWARE_MAPPING = "adafruit-hat"
# Value that worked at first light (Iteration 1).
GPIO_SLOWDOWN = 2
BRIGHTNESS = 50  # percent


def create_matrix() -> RGBMatrix:
    options = RGBMatrixOptions()
    options.rows = ROWS
    options.cols = COLS
    options.hardware_mapping = HARDWARE_MAPPING
    options.gpio_slowdown = GPIO_SLOWDOWN
    options.brightness = BRIGHTNESS
    return RGBMatrix(options=options)
