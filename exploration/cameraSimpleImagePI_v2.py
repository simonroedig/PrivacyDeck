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

# ===== HELPER FUNCTIONS =====
def show(msg, color=TFT.WHITE):
    """Show multi-line message on TFT, truncate if too long."""
    tft.fill(TFT.BLACK)
    max_chars = WIDTH // 6
    lines = []
    for line in msg.split("\n"):
        # split line if too long
        for i in range(0, len(line), max_chars):
            lines.append(line[i:i+max_chars])
    for i, l in enumerate(lines):
        tft.text((5, 10 + i*10), l, color, sysfont)

# ===== READY MESSAGE =====
print("TFT Ready")
show("Waiting for\nPython daemon", TFT.GREEN)

# ===== PREALLOCATE LINE BUFFER =====
line_buf = bytearray(WIDTH * 2)  # one line at a time for RGB565

# ===== SERIAL IMAGE RECEIVER =====
while True:
    try:
        gc.collect()  # free memory before receiving
        line = sys.stdin.readline()

        if not line:
            continue

        if line.startswith("IMG"):
            show("Receiving image...", TFT.YELLOW)
            parts = line.strip().split(",")
            w = int(parts[1])
            h = int(parts[2])
            size = int(parts[3])

            if w != WIDTH or h != HEIGHT:
                raise ValueError("Unexpected image size")

            print("Expect bytes:", size)

            # ---- STREAM IMAGE LINE BY LINE ----
            for y in range(HEIGHT):
                idx = 0
                while idx < WIDTH * 2:
                    chunk = sys.stdin.buffer.read(WIDTH*2 - idx)
                    if chunk:
                        line_buf[idx:idx+len(chunk)] = chunk
                        idx += len(chunk)
                tft.image(0, y, WIDTH-1, y, line_buf)  # draw one line

            print("Image drawn")
            show("Image drawn!", TFT.CYAN)

    except Exception as e:
        err_msg = str(e)
        print("ERROR:", err_msg)
        show("ERROR:\n" + err_msg)
