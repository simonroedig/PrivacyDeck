from machine import Pin, SPI
from privacyDeck.lib import ST7735
import time

# 1. Setup SPI 1 based on your pinout
# SCK=19, MOSI(SDA)=14, MISO is not used for display but required for SPI init
spi = SPI(1, baudrate=20000000, polarity=0, phase=0, sck=Pin(14), mosi=Pin(15))

# 2. Define Control Pins
tft_cs = Pin(13, Pin.OUT)
tft_res = Pin(12, Pin.OUT)
tft_dc = Pin(11, Pin.OUT)
# Backlight - Pin 36 is constant 3.3V, but if you used a GPIO, you'd set it High here

# 3. Initialize Display
# 128x160 is standard for 1.8" TFT
display = ST7735.TFT(spi, tft_cs, tft_dc, tft_res)
display.init()

def display_image(filename):
    try:
        with open(filename, 'rb') as f:
            # We draw in chunks to save RAM on the Pico
            for row in range(160):
                # Each pixel is 2 bytes (RGB565), so 128 pixels * 2 = 256 bytes per row
                buffer = f.read(128 * 2)
                if not buffer:
                    break
                display.blit_buffer(buffer, 0, row, 128, 1)
    except OSError:
        print("Image file not found. Please upload 'image.raw'")

# Clear screen to black and show image
display.fill(0)
display_image('image.raw')