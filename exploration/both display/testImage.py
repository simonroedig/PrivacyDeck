from machine import Pin, SPI
import time
import ST7735
import os

# ==========================================
# DISPLAY 1 SETUP (The "Red" Display)
# ==========================================
spi1 = SPI(1, baudrate=24_000_000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11))
cs1  = Pin(9, Pin.OUT)
dc1  = Pin(12, Pin.OUT)
rst1 = Pin(13, Pin.OUT)

display1 = ST7735.TFT(spi1, dc1, rst1, cs1)

# .initr() often defaults to 128x160. 
# If your screen is 160x80 or 160x128, we use initg() or a specific rotation.
display1.initr() 
display1.rotation(1) # Try 1 or 3 for horizontal

# Adjust these based on your specific bin file
IMG_WIDTH = 160
IMG_HEIGHT = 128 # Change to 80 if this is the small display
FILENAME = "avatar2_fullcamera.bin"

# Most 160x80/128 screens have a hardware offset 
# because the chip supports 132x162 but the glass is smaller.
OFFSET_X = 1  # Try 0, 1, or 26 if the image is shifted
OFFSET_Y = 26 # Common offset for horizontal ST7735 screens

def draw_bin_image(display, filename):
    if filename not in os.listdir():
        print("File not found!")
        return

    with open(filename, "rb") as f:
        row_size = IMG_WIDTH * 2
        for y in range(IMG_HEIGHT):
            row_data = f.read(row_size)
            if not row_data:
                break
            
            # We use the offset here to "push" the image into the visible area
            display.image(OFFSET_X, y + OFFSET_Y, IMG_WIDTH + OFFSET_X - 1, y + OFFSET_Y, row_data)

# ==========================================
# MAIN LOOP
# ==========================================
display1.fill(0x0000)

print("Displaying avatar...")
while True:
    draw_bin_image(display1, FILENAME)
    time.sleep(5)
