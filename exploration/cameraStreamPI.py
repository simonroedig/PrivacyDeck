from machine import Pin, SPI
from ST7735 import TFT
import sys
import gc
import micropython

# Disable Ctrl+C handling so binary data doesn't stop the script
micropython.kbd_intr(-1)

# ===== DISPLAY SETUP =====
spi = SPI(1, baudrate=20000000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11))
tft = TFT(spi, 16, 17, 18)
tft.initr()
tft.rotation(1)
tft.fill(TFT.BLACK)

WIDTH = 160
HEIGHT = 128
EXPECTED_SIZE = WIDTH * HEIGHT * 2

# ===== PREALLOCATE BUFFER =====
data = bytearray(EXPECTED_SIZE)

print("PICO_READY") # Tell computer we are powered on

while True:
    try:
        # 1. Look for the 4-byte sync header "IMG!"
        # We use read(1) to "hunt" for the start if we get out of sync
        header = sys.stdin.buffer.read(4)
        if header != b'IMG!':
            continue 

        # 2. Read the full image data (fixed size)
        idx = 0
        while idx < EXPECTED_SIZE:
            chunk = sys.stdin.buffer.read(EXPECTED_SIZE - idx)
            if chunk:
                data[idx:idx+len(chunk)] = chunk
                idx += len(chunk)

        # 3. Draw immediately
        tft.image(0, 0, WIDTH-1, HEIGHT-1, data)

        # 4. Signal computer to send next frame
        sys.stdout.write("READY\n")
        
        gc.collect()

    except Exception as e:
        # If error occurs, we don't print to avoid mess, just try to keep going
        pass
