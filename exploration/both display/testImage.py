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

# Clear the screens (fixes static/noise)
display1.fill(BLACK)
display2.fill(BLUE)

# ==========================================
# FAST BMP LOADER
# ==========================================
def draw_bmp_to_display1(filename):
    print(f"Loading {filename}...")
    try:
        f = open(filename, "rb")
    except OSError:
        print(f"Error: {filename} not found on the Pico!")
        return

    # 1. Parse BMP Header
    header = f.read(54)
    if header[0:2] != b'BM':
        print("Error: Not a valid BMP file.")
        f.close()
        return
        
    data_offset = int.from_bytes(header[10:14], 'little')
    width = int.from_bytes(header[18:22], 'little')
    height_bytes = header[22:26]
    height = int.from_bytes(height_bytes, 'little')
    
    # Negative height means top-down image
    top_down = False
    if height > 0x7FFFFFFF: 
        height = 0x100000000 - height
        top_down = True
        
    bpp = int.from_bytes(header[28:30], 'little')
    if bpp not in (16, 24):
        print(f"Error: Unsupported depth ({bpp}bpp). Please use a 24-bit BMP.")
        f.close()
        return
        
    print(f"Processing Image: {width}x{height} @ {bpp}bpp")
    
    row_bytes = ((width * bpp + 31) // 32) * 4
    f.seek(data_offset)
    
    # 2. Allocate memory buffer for the physical portrait display (128x160)
    # The Pi Pico has enough RAM to hold this entirely in memory for a fast SPI upload
    buf = bytearray(128 * 160 * 2)
    
    # 3. Read image, convert colors to 16-bit RGB565, and rotate it 90 degrees
    #    so that your horizontal 160x128 image fits the 128x160 physical layout.
    for r in range(height):
        # BMP rows are bottom-to-top by default
        r_mapped = (127 - r) if top_down else r
        
        row_data = f.read(row_bytes)
        
        # Prevent overflowing buffer if image is slightly larger
        if r_mapped >= 128: continue
            
        for c in range(width):
            if c >= 160: continue
                
            if bpp == 24:
                # 24-bit (Blue, Green, Red)
                b = row_data[c*3]
                g = row_data[c*3 + 1]
                r_col = row_data[c*3 + 2]
                color = ((r_col & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            else:
                # 16-bit BMP native
                color = row_data[c*2] | (row_data[c*2 + 1] << 8)
            
            # Map 160x128 Landscape to 128x160 Portrait Array
            idx = (c * 128 + r_mapped) * 2
            buf[idx] = color >> 8
            buf[idx+1] = color & 0xFF
            
    f.close()
    
    print("Uploading to Red Webcam Screen via Fast SPI...")
    
    # 4. Use raw SPI commands to define screen writing area (X:0-127, Y:0-159)
    x0, x1 = 0, 127
    y0, y1 = 0, 159
    
    cs1.value(0)
    
    # CASET (Set Column Address)
    dc1.value(0)
    spi1.write(b'\x2A')
    dc1.value(1)
    spi1.write(bytearray([0, x0, 0, x1]))
    
    # RASET (Set Row Address)
    dc1.value(0)
    spi1.write(b'\x2B')
    dc1.value(1)
    spi1.write(bytearray([0, y0, 0, y1]))
    
    # RAMWR (Memory Write)
    dc1.value(0)
    spi1.write(b'\x2C')
    dc1.value(1)
    
    # 5. Blast the entire rotated image frame into the screen!
    spi1.write(buf)
    cs1.value(1)
    
    print("Image displayed successfully!")

# ==========================================
# MAIN EXECUTION
# ==========================================

# Display the BMP image on the "Red" webcam screen
draw_bmp_to_display1("test.bmp")

while True:
    # Keep the script running (add logic for the mic screen here later if needed)
    time.sleep(1)
