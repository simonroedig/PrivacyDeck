from machine import Pin, SPI
from ST7735 import TFT
from sysfont import sysfont
import sys
import time
import gc

# ===== DISPLAY SETUP =====
spi = SPI(1, baudrate=20000000, polarity=0, phase=0,
          sck=Pin(10), mosi=Pin(11))

tft = TFT(spi, 16, 17, 18)
tft.initr()
tft.rotation(1)
tft.fill(TFT.BLACK)

WIDTH = 160
HEIGHT = 128

def show(msg, color=TFT.WHITE):
    tft.fill(TFT.BLACK)
    tft.text((5,10), msg, color, sysfont)

print("TFT Ready")
show("Waiting for\nPython daemon", TFT.GREEN)

# ===== SERIAL IMAGE RECEIVER =====
# preallocate once
data = bytearray(WIDTH * HEIGHT * 2)

while True:
    try:
        gc.collect()  # still good to call
        line = sys.stdin.readline()

        if not line:
            continue

        if line.startswith("IMG"):
            show("Receiving image...", TFT.YELLOW)

            parts = line.strip().split(",")
            w = int(parts[1])
            h = int(parts[2])
            size = int(parts[3])

            if size > len(data):
                # just in case, resize once
                data = bytearray(size)

            print("Expect bytes:", size)

            # ---- READ IMAGE DATA ----
            idx = 0
            while idx < size:
                chunk = sys.stdin.buffer.read(size - idx)
                if chunk:
                    data[idx:idx+len(chunk)] = chunk
                    idx += len(chunk)

            print("Image received")

            # ---- DRAW IMAGE FAST ----
            tft.image(0, 0, w-1, h-1, data)
            
            time.sleep(3)

            show("Image drawn!", TFT.CYAN)

    except Exception as e:
        err_msg = str(e)
        print("ERROR:", err_msg)
        show("ERROR:\n" + err_msg[:WIDTH//6*5], TFT.RED)


