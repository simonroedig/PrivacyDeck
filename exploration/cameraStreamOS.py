import serial
import time
import cv2
import numpy as np

PORT = "COM8"
WIDTH = 160
HEIGHT = 128
BAUDRATE = 500000 

# Open serial with a 2-second timeout so it doesn't freeze forever
ser = serial.Serial(PORT, BAUDRATE, timeout=2)
time.sleep(2)

cap = cv2.VideoCapture(0)
# Set capture resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

print("Starting robust webcam stream...")

def rgb_to_rgb565(frame):
    """Optimized conversion for ST7735 (Big Endian)."""
    # Resize if the webcam didn't respect the CAP_PROP settings
    if frame.shape[0] != HEIGHT or frame.shape[1] != WIDTH:
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
    
    frame = frame.astype(np.uint16)
    r = (frame[:, :, 0] & 0xF8) << 8
    g = (frame[:, :, 1] & 0xFC) << 3
    b = (frame[:, :, 2] >> 3)
    rgb565 = np.bitwise_or(np.bitwise_or(r, g), b)
    # Most ST7735 drivers need the bytes swapped (Big Endian)
    return rgb565.byteswap().tobytes()

try:
    # Clear any junk in the buffer
    ser.reset_input_buffer()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Convert BGR (OpenCV) to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        buf = rgb_to_rgb565(frame_rgb)

        # 1. Send fixed header (exactly 4 bytes)
        ser.write(b'IMG!')
        
        # 2. Send image data
        ser.write(buf)
        ser.flush()

        # 3. Wait for "READY" with timeout
        # If Pico doesn't reply in 2 seconds, we just try the next frame
        line = ser.readline().decode().strip()
        
        if "READY" in line:
            # Frame handled successfully
            continue
        else:
            print("Frame dropped or timeout - Resyncing...")
            ser.reset_input_buffer()

finally:
    cap.release()
    ser.close()