from machine import Pin, SPI
from ST7735 import TFT
import time

# 1. Setup SPI1 (Note the '1' here instead of '0')
# SCK is GP10, SDA(MOSI) is GP11
spi = SPI(1, baudrate=20000000, polarity=0, phase=0, 
          sck=Pin(10), mosi=Pin(11))

# 2. Setup Control Pins
# A0/DC=16, Reset=17, CS=18
tft = TFT(spi, 16, 17, 18)

print("Initializing...")

# 3. Try the 'Red Tab' initialization first
tft.initr() 
tft.fill(TFT.BLACK)

# 4. Draw a test pattern
tft.fill(TFT.BLUE) # Screen should turn Blue
time.sleep(1)
tft.rect((20, 20), (40, 40), TFT.WHITE) # Draw a white square
tft.line((0, 0), (128, 160), TFT.RED)    # Draw a red diagonal line

print("Done! If the screen is still black, check the LED pin connection.")
