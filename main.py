from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw

options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 2   # try 2 first, then 1, then 4
options.brightness = 50

matrix = RGBMatrix(options=options)

img = Image.new("RGB", (64, 64))
draw = ImageDraw.Draw(img)
for x in range(64):
    for y in range(64):
        img.putpixel((x, y), (x * 4, y * 4, 128))
draw.rectangle([0, 0, 63, 63], outline=(255, 255, 255))
draw.line([0, 0, 63, 63], fill=(255, 0, 0))
draw.line([0, 63, 63, 0], fill=(255, 0, 0))

matrix.SetImage(img)
input("Showing test pattern. Press Enter to exit...")