import socket
import network
import _thread
import time
import gc
from machine import SPI, Pin
from privacyDeck.lib.ST7735 import TFT

# --- 1. WiFi Setup ---
WIFI_SSID = ""
WIFI_PASS = ""

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# Power management: 0xa11140 is valid for Cypress chips (Pico W),
# but Pico 2 W uses a different chip. If this throws an error, comment it out.
try:
    wlan.config(pm=0xa11140)
except:
    pass  # Ignore if PM config fails on Pico 2

wlan.connect(WIFI_SSID, WIFI_PASS)

print("Connecting...")
max_wait = 15
while max_wait > 0:
    if wlan.isconnected(): break
    max_wait -= 1
    time.sleep(1)

if not wlan.isconnected():
    print("WiFi Failed")
    # Blink LED to signal error if needed
else:
    print(f"IP: {wlan.ifconfig()[0]}")

# --- 2. Display Setup ---
# ST7735 Driver Setup
spi = SPI(1, baudrate=60_000_000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
tft = TFT(spi, 14, 15, 13)
tft.initr()
tft.rgb(True)
tft.fill(0)
tft._setwindowloc((0, 0), (127, 159))

# --- 3. Double Buffering & Shared State ---
FRAME_SIZE = 128 * 160 * 2
CHUNK_SIZE = 1024

# Two big buffers
buffer0 = bytearray(FRAME_SIZE)
buffer1 = bytearray(FRAME_SIZE)

# References to buffers
write_buffer = buffer0
display_buffer = buffer1

# Shared Flags: [NewFrameReady (Bool)]
# We use a list so it is mutable and shared safely between threads
flags = [False]
thread_lock = _thread.allocate_lock()


# --- 4. Core 1: Display Thread ---
def display_thread():
    while True:
        # Check if a new frame is ready
        if flags[0]:
            thread_lock.acquire()
            # Swap happens in main thread, we just grab the display_buffer
            # We create a memoryview locally to ensure we hold the reference
            current_view = display_buffer
            flags[0] = False  # Reset flag
            thread_lock.release()

            # Send to screen (Blocking High-Speed SPI)
            tft._writedata(current_view)
        else:
            # Important: Short sleep to yield execution
            time.sleep(0.001)


# Start thread BEFORE main loop
_thread.start_new_thread(display_thread, ())

# --- 5. Core 0: UDP Receiver ---
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('0.0.0.0', 5005))
s.settimeout(1.0)  # Non-blocking with 1s timeout to keep loop alive

print("UDP LISTENING...")

# Pre-allocate input buffer (Header + Data)
packet_buf = bytearray(1026)
write_view = memoryview(write_buffer)

current_frame_id = -1
chunks_received = 0

try:
    while True:
        try:
            # READINTO: Zero-copy read.
            # Note: readinto might lose the sender address, but we save RAM/CPU
            nbytes = s.readinto(packet_buf)
        except OSError:
            # Timeout or no data
            continue

        # Basic validation
        if nbytes != 1026:
            continue

        # Header: [Frame ID, Chunk ID]
        fid = packet_buf[0]
        cid = packet_buf[1]

        # Sync logic
        if fid != current_frame_id:
            current_frame_id = fid
            chunks_received = 0

        # Copy Pixel Data
        start = cid * CHUNK_SIZE
        end = start + CHUNK_SIZE

        # Write directly into the write_buffer
        # packet_buf[2:] is the payload
        write_view[start:end] = packet_buf[2:nbytes]

        # Check for End of Frame (Chunk 39)
        if cid == 39:
            thread_lock.acquire()
            # SWAP BUFFERS
            # The 'write_buffer' becomes the 'display_buffer'
            temp = write_buffer
            write_buffer = display_buffer
            display_buffer = temp

            # Update the view so next writes go to the new empty buffer
            write_view = memoryview(write_buffer)

            # Signal Core 1 to draw
            flags[0] = True
            thread_lock.release()

except Exception as e:
    print("Core 0 Error:", e)
finally:
    s.close()