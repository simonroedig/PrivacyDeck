from machine import Pin, SPI
import time
import ST7735

# --- Color Definitions (RGB565 format) ---
RED    = 0xF800
GREEN  = 0x07E0
BLUE   = 0x001F
YELLOW = 0xFFE0
WHITE  = 0xFFFF
BLACK  = 0x0000

# ==========================================
# DISPLAY 1 (Red / Webcam - 128x160) - SPI1
# ==========================================
spi1 = SPI(1, baudrate=20_000_000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11))
cs1  = Pin(9, Pin.OUT)
dc1  = Pin(12, Pin.OUT)
rst1 = Pin(13, Pin.OUT)

display1 = ST7735.TFT(spi1, dc1, rst1, cs1)
display1.initr() 

# ==========================================
# DISPLAY 2 (Blue / Mic - 160x80) - SPI0
# ==========================================
spi0 = SPI(0, baudrate=20_000_000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19))
cs2  = Pin(17, Pin.OUT)
dc2  = Pin(20, Pin.OUT)
rst2 = Pin(21, Pin.OUT)

display2 = ST7735.TFT(spi0, dc2, rst2, cs2)
display2.initr()

# ==========================================
# TEST LOOP
# ==========================================
print("Starting display test...")

# Your display's secret X offset (usually 24 or 26)
# If the white border is cut off on the left or right edge, change this to 26!
OFFSET_X = 24 
OFFSET_Y = 0

while True:
    print("Colors: Red / Blue")
    display1.fill(RED)
    display2.fill(BLUE) # Clears all the static/noise!
    
    # Draw a white box. Notice the extra parentheses for (X,Y) and (Width,Height)!
    display2.rect((OFFSET_X, OFFSET_Y), (80, 160), WHITE)
    
    time.sleep(2)

    print("Colors: Blue / Red")
    display1.fill(BLUE)
    display2.fill(RED)
    
    # Draw the white bounding box again
    display2.rect((OFFSET_X, OFFSET_Y), (80, 160), WHITE)
    
    time.sleep(2)
