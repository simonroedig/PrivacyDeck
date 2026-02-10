import serial
import time
from PIL import Image

PORT = "COM8"
WIDTH = 160
HEIGHT = 128

print("Opening serial...")
ser = serial.Serial(PORT, 115200)
time.sleep(2)

print("Loading image...")
img = Image.open("test.jpg").convert("RGB")
img = img.resize((WIDTH, HEIGHT))

# Convert to RGB565
buf = bytearray()

for y in range(HEIGHT):
    for x in range(WIDTH):
        r, g, b = img.getpixel((x, y))
        color = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        buf.append(color >> 8)
        buf.append(color & 0xFF)

print("Sending header...")
ser.write(f"IMG,{WIDTH},{HEIGHT},{len(buf)}\n".encode())

time.sleep(0.2)

print("Sending image...")
ser.write(buf)

print("Done!")
ser.close()
