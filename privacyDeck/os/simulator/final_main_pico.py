import machine
from machine import Pin, ADC, SPI
import time
import json
import neopixel
import ST7735
import math
import random

# --- Color Definitions (RGB565) ---
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F
YELLOW = 0xFFE0
BLACK = 0x0000
WHITE = 0xFFFF

# ==========================================
# MACRO PAD CONFIGURATION
# ==========================================
BUTTONS = {
    0: {"name": "Button 1", "func": "Lock OS"},
    1: {"name": "Button 2", "func": "browser clean"},
    2: {"name": "Button 3", "func": "gps mode"},
    3: {"name": "Button 4", "func": "wipe clipboard history"},
    4: {"name": "Button 5", "func": "Instant Privacy"}
}

TOGGLES = {
    5: {"name": "Toggle 1", "func": "usb alert"},
    6: {"name": "Toggle 2", "func": "blackout/presentation mode"},
    7: {"name": "Toggle 3", "func": "airplane mode"},
    8: {"name": "Toggle 4", "func": "mic mute toggle"}
}

DEBOUNCE_DELAY = 50

# ==========================================
#Slider Configuration
# ==========================================

slider = ADC(27)
last_slider_value = -1

# ==========================================
# AVATAR CONFIGURATION
# ==========================================
NUM_LEDS = 7
NEO_PIN = 28
ADC_PIN = 26

# Thresholds for Avatar Recognition
NO_AVATAR_MAX = 0.9
AV1_47K_MIN = 0.95
AV1_47K_MAX = 1.2
AV2_20K_MIN = 1.5
AV2_20K_MAX = 1.7  # leave headroom below 3.3 V

AVATAR_LED_MAP = {
    "head": [2, 3, 5, 6],
    "eyes": [1, 4],
    "mouth": [0]
}

active_pulsing_parts = {}
last_pulse_update = 0
pulse_angle = 0.0
PULSE_INTERVAL = 30  # Milliseconds between updates (approx 33 fps)
PULSE_SPEED = 0.1  # How much the angle increments per frame

COLOR_OFF = (0, 0, 0)
COLOR_AV1 = (0, 100, 225)  # blue
COLOR_AV2 = (255, 100, 0)  # yellow
RGB_WHITE = (255, 255, 255)
RGB_RED = (255, 0, 0)
RGB_GREEN = (0, 255, 0)
RGB_BLUE = (0, 0, 255)
RGB_YELLOW = (255, 255, 0)

# --- FADE CONFIGURATION ---
fade_start_time = 0
is_fading = False
fade_duration = 3000
current_base_head_color = COLOR_OFF

# ==========================================
# SPI Display 1 (Red / Webcam)
# ==========================================
spi1 = SPI(1, baudrate=20_000_000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11))
cs1 = Pin(9, Pin.OUT)
dc1 = Pin(12, Pin.OUT)
rst1 = Pin(13, Pin.OUT)

display1 = ST7735.TFT(spi1, dc1, rst1, cs1)
display1.initr()

# ==========================================
# DISPLAY 2 (Blue / Mic - 160x80) - SPI0
# ==========================================
spi0 = SPI(0, baudrate=20_000_000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19))
cs2 = Pin(17, Pin.OUT)
dc2 = Pin(20, Pin.OUT)
rst2 = Pin(21, Pin.OUT)

display2 = ST7735.TFT(spi0, dc2, rst2, cs2)
display2.initr()
display1.fill(BLACK)
display2.fill(BLACK)

# ==========================================
# AUDIO METER CONFIGURATION (DISPLAY 2) - PORTRAIT
# ==========================================
METER_COLS = 12
METER_ROWS = 16
COL_WIDTH = 8
COL_SPACING = 2
ROW_HEIGHT = 6
ROW_SPACING = 2
METER_UPDATE_INTERVAL = 60

# If the display leaves a gap on the side, adjust this offset (commonly 24 or 26 for 80x160 screens)
METER_X_OFFSET = 0
METER_Y_OFFSET = 0

# FIXED: Using 16-bit RGB565 integers instead of tuples
METER_COLORS = [WHITE] * 14 + [RED] * 2

meter_state = [0] * METER_COLS
last_meter_update = 0
meter_is_cleared = False

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def custom_fill_rect(spi_bus, dc, cs, x, y, w, h, color):
    """Raw SPI rectangle drawing to bypass missing library methods."""
    x0, x1 = x, x + w - 1
    y0, y1 = y, y + h - 1

    cs.value(0)

    # Set Column Address
    dc.value(0)
    spi_bus.write(b'\x2A')
    dc.value(1)
    spi_bus.write(bytearray([0, x0, 0, x1]))

    # Set Row Address
    dc.value(0)
    spi_bus.write(b'\x2B')
    dc.value(1)
    spi_bus.write(bytearray([0, y0, 0, y1]))

    # Memory Write
    dc.value(0)
    spi_bus.write(b'\x2C')
    dc.value(1)

    # Prepare and send color buffer
    color_high = color >> 8
    color_low = color & 0xFF

    buf = bytearray([color_high, color_low] * (w * h))

    spi_bus.write(buf)
    cs.value(1)


def update_audio_meter(avatar_state):
    """Generates a bouncing audio matrix effect on Display 2."""
    global last_meter_update, meter_state, meter_is_cleared

    # Check Toggle 4 (Mic Mute). If it is in state '1' (Muted), hide the meter.
    if button_states_new.get("Toggle 4", 0) == 0 or avatar_state == "none":
        if not meter_is_cleared:
            display2.fill(BLACK)
            meter_state = [0] * METER_COLS
            meter_is_cleared = True
        return

    meter_is_cleared = False

    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_meter_update) < METER_UPDATE_INTERVAL:
        return

    for col in range(METER_COLS):
        old_val = meter_state[col]

        # Randomly change the level
        change = random.randint(-4, 4)
        new_val = old_val + change

        if new_val < 0: new_val = 0
        if new_val > METER_ROWS: new_val = METER_ROWS

        if new_val > old_val:
            for r in range(old_val, new_val):
                # Inverted calculation: Starts at 0 and builds up
                y = METER_Y_OFFSET + r * (ROW_HEIGHT + ROW_SPACING) + ROW_SPACING
                x = METER_X_OFFSET + col * (COL_WIDTH + COL_SPACING) + (COL_SPACING // 2)
                custom_fill_rect(spi0, dc2, cs2, x, y, COL_WIDTH, ROW_HEIGHT, METER_COLORS[r])
        elif new_val < old_val:
            for r in range(new_val, old_val):
                y = METER_Y_OFFSET + r * (ROW_HEIGHT + ROW_SPACING) + ROW_SPACING
                x = METER_X_OFFSET + col * (COL_WIDTH + COL_SPACING) + (COL_SPACING // 2)
                custom_fill_rect(spi0, dc2, cs2, x, y, COL_WIDTH, ROW_HEIGHT, BLACK)

        meter_state[col] = new_val

    last_meter_update = current_time

def interpolate_color(color_start, color_end, elapsed, duration):
    """Calculates the intermediate color using safe integer math."""
    r = color_start[0] + (color_end[0] - color_start[0]) * elapsed // duration
    g = color_start[1] + (color_end[1] - color_start[1]) * elapsed // duration
    b = color_start[2] + (color_end[2] - color_start[2]) * elapsed // duration
    return (r, g, b)


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
                b = row_data[c * 3]
                g = row_data[c * 3 + 1]
                r_col = row_data[c * 3 + 2]
                color = ((r_col & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            else:
                # 16-bit BMP native
                color = row_data[c * 2] | (row_data[c * 2 + 1] << 8)

            # Map 160x128 Landscape to 128x160 Portrait Array
            idx = (c * 128 + r_mapped) * 2
            buf[idx] = color >> 8
            buf[idx + 1] = color & 0xFF

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


def draw_bin(display, filename):
    """Streams a raw RGB565 .bin file to the display"""
    try:
        # Set the drawing window to full screen (128x160)
        display.setAddrWindow(0, 0, 127, 159)
        with open(filename, "rb") as f:
            chunk = f.read(2048)
            while chunk:
                display.data(chunk)
                chunk = f.read(2048)
    except Exception:
        display.fill(RED)  # Fallback if file is missing


def set_color(led_mapping):
    for led_index, color in led_mapping.items():
        np[led_index] = color
    np.write()


def update_pulsing():
    global last_pulse_update, pulse_angle

    if not active_pulsing_parts:
        return

    current_time = time.ticks_ms()

    # Throttle the LED updates to prevent protocol jamming
    if time.ticks_diff(current_time, last_pulse_update) >= PULSE_INTERVAL:

        # Increment the angle and wrap it at 2*Pi to prevent float overflow
        pulse_angle += PULSE_SPEED
        if pulse_angle > math.pi * 2:
            pulse_angle -= math.pi * 2

        # Calculate brightness: maps -1.0 to 1.0 sine wave to 0.5 to 1.0 multiplier
        wave = math.sin(pulse_angle)
        brightness = 0.75 + (wave * 0.25)

        for part, base_color in active_pulsing_parts.items():
            indices = AVATAR_LED_MAP[part]
            r = int(base_color[0] * brightness)
            g = int(base_color[1] * brightness)
            b = int(base_color[2] * brightness)

            for i in indices:
                np[i] = (r, g, b)

        np.write()
        last_pulse_update = current_time


def set_avatar_color(color_dict):
    for part, config in color_dict.items():
        indices = AVATAR_LED_MAP[part]
        color = config.get("color")
        is_pulsing = config.get("pulsing", False)

        if is_pulsing:
            active_pulsing_parts[part] = color
        else:
            active_pulsing_parts.pop(part, None)
            for i in indices:
                np[i] = color
    np.write()


def send_serial(component_type, pin_num, name, func, state):
    data = {"type": component_type, "pin": pin_num, "name": name, "function": func, "button_states": state, "avatar": current_avatar_state}
    print(json.dumps(data))


# ==========================================
# INITIALIZATION
# ==========================================
pins = {}
button_states_new = {}
last_debounce_time = {}
color_to_fade = None
slider_percent = 0
current_displayed_image = ""

for pin_num, config in list(BUTTONS.items()) + list(TOGGLES.items()):
    pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
    pins[pin_num] = pin
    name = config["name"]
    button_states_new[name] = pin.value()
    last_debounce_time[pin_num] = 0

for name, value in button_states_new.items():
    if value == 1:
        state = "ON"
    else :
        state = "OFF"
    print(f"{name} has state {state}")

np = neopixel.NeoPixel(Pin(NEO_PIN), NUM_LEDS)
adc = ADC(ADC_PIN)

set_color({i: COLOR_OFF for i in range(NUM_LEDS)})
display1.fill(RED)
print(json.dumps({"info": "Pico Macro Pad & Displays Started"}))

# Main Loop Variables
voltage_samples = []
last_adc_read_time = 0
last_avatar_eval_time = 0
current_avatar_state = "none"  # Forces the avatar code to set the base color immediately

ADC_SAMPLE_INTERVAL = 4
AVATAR_EVAL_INTERVAL = 400

# ==========================================
# MAIN LOOP
# ==========================================
while True:
    current_time = time.ticks_ms()

    # 1. CHECK PUSH BUTTONS
    for pin_num in BUTTONS.keys():
        name = BUTTONS[pin_num]["name"]
        current_value = pins[pin_num].value()
        if current_value != button_states_new[name]:
            if time.ticks_diff(current_time, last_debounce_time[pin_num]) > DEBOUNCE_DELAY:
                if current_value == 0:
                    send_serial("button", pin_num, name, BUTTONS[pin_num]["func"], "pressed")

                    # --- START FADE TRIGGER ---
                    print(f"{name} should assign color")
                    is_fading = True
                    fade_start_time = current_time
                    if name == "Button 1":
                        color = COLOR_OFF
                    elif name == "Button2":
                        color = RGB_WHITE
                    elif name == "Button 3":
                        color = RGB_BLUE
                    elif name == "Button 4":
                        color = RGB_RED
                    elif name == "Button 5":
                        color = RGB_RED
                    else:
                        color = RGB_WHITE
                    color_to_fade = color
                    for i in AVATAR_LED_MAP["head"]:
                        np[i] = color
                    np.write()
                    # --------------------------

                button_states_new[name] = current_value
                last_debounce_time[pin_num] = current_time

    # 2. CHECK TOGGLES
    for pin_num in TOGGLES.keys():
        name = TOGGLES[pin_num]["name"]
        current_value = pins[pin_num].value()
        if current_value != button_states_new[name]:
            if time.ticks_diff(current_time, last_debounce_time[pin_num]) > DEBOUNCE_DELAY:
                state_str = "ON" if current_value == 0 else "OFF"
                send_serial("toggle", pin_num, name, TOGGLES[pin_num]["func"], state_str)
                button_states_new[name] = current_value
                last_debounce_time[pin_num] = current_time

    # Update Mouth Color based on Toggle 4 (Only triggers when necessary)
    mouth_target = RGB_RED if button_states_new.get("Toggle 4", 0) == 1 else COLOR_OFF
    if np[AVATAR_LED_MAP["mouth"][0]] != mouth_target:
        set_avatar_color({"mouth": {"color": mouth_target, "pulsing": False}})

    # 3. NON-BLOCKING ADC SAMPLING
    if time.ticks_diff(current_time, last_adc_read_time) >= ADC_SAMPLE_INTERVAL:
        voltage_samples.append(adc.read_u16())
        if len(voltage_samples) > 8:
            voltage_samples.pop(0)
        last_adc_read_time = current_time

    # 4. AVATAR & DISPLAY LOGIC
    if time.ticks_diff(current_time, last_avatar_eval_time) >= AVATAR_EVAL_INTERVAL:
        if len(voltage_samples) == 8:
            avg_raw = sum(voltage_samples) / 8
            v = (avg_raw / 65535) * 3.3

            new_state = "none"
            new_color = {i: COLOR_OFF for i in range(NUM_LEDS)}

            if v <= NO_AVATAR_MAX:
                new_state = "none"
                print("no av")
                new_colour = {
                    "head": {"color": COLOR_OFF, "pulsing": False},
                    "eyes": {"color": COLOR_OFF, "pulsing": False},
                    "mouth": {"color": COLOR_OFF, "pulsing": False}
                }
            elif AV1_47K_MIN <= v <= AV1_47K_MAX:
                new_state = "av1"
                print("av1")
                new_colour = {
                    "head": {"color": COLOR_AV1, "pulsing": False},
                    "eyes": {"color": COLOR_OFF, "pulsing": True},
                    "mouth": {"color": COLOR_OFF, "pulsing": False}
                }
            elif AV2_20K_MIN <= v <= AV2_20K_MAX:
                new_state = "av2"
                print("av2")
                new_colour = {
                    "head": {"color": COLOR_AV2, "pulsing": False},
                    "eyes": {"color": COLOR_OFF, "pulsing": True},
                    "mouth": {"color": COLOR_OFF, "pulsing": False}
                }
            else:
                new_state = "none"
                print("no av")
                new_colour = {
                    "head": {"color": COLOR_OFF, "pulsing": False},
                    "eyes": {"color": COLOR_OFF, "pulsing": False},
                    "mouth": {"color": COLOR_OFF, "pulsing": False}
                }

            # EXECUTE CHANGE
            if new_state != current_avatar_state:
                set_avatar_color(new_colour)

                # Update our fade target so it always knows what color to return to
                current_base_head_color = new_colour["head"]["color"]
                current_avatar_state = new_state

        last_avatar_eval_time = current_time

    slider_value = slider.read_u16()
    if abs(slider_value - last_slider_value) > 2000:
        slider_percent = (slider_value / 65535) * 100
        print(f"[SLIDER] Value: {slider_value} ({slider_percent:.1f}%)")
        last_slider_value = slider_value
    target_image = current_displayed_image  # Default to no change
    if current_avatar_state == "none":
        target_image = "no_avatar.bmp"
    else:
        if slider_percent < 25:
            target_image = "avatar1_on.bmp" if current_avatar_state == "av1" else "avatar2_on.bmp"
        elif 25 <= slider_percent <= 50:
            target_image = "avatar1_blur1.bmp" if current_avatar_state == "av1" else "avatar2_blur1.bmp"
        elif slider_percent <= 75:
            target_image = "avatar1_blur2.bmp" if current_avatar_state == "av1" else "avatar2_blur2.bmp"
        elif slider_percent > 75:
            target_image = "avatar1_off.bmp" if current_avatar_state == "av1" else "avatar2_off.bmp"

    # Only draw to the screen if the target image is different from the currently displayed image
    if target_image != current_displayed_image:
        if target_image != "":  # Prevent blank loads on initial startup
            draw_bmp_to_display1(target_image)
        current_displayed_image = target_image

    # Evaluate target color based on slider percentage
    if slider_percent < 75:
        eyes_target = RGB_RED
    elif slider_percent > 75:
        eyes_target = COLOR_OFF
    else:
        eyes_target = None  # No change to LED state between 25% and 75%

    # Apply color if a target is defined and the current state doesn't match
    if eyes_target is not None and np[AVATAR_LED_MAP["eyes"][0]] != eyes_target:
        set_avatar_color({"eyes": {"color": eyes_target, "pulsing": False}})


    # 5. EXECUTE FADE LOGIC
    if is_fading:
        elapsed = time.ticks_diff(current_time, fade_start_time)
        if elapsed < fade_duration:
            current_fade_color = interpolate_color(color_to_fade, current_base_head_color, elapsed, fade_duration)
            for i in AVATAR_LED_MAP["head"]:
                np[i] = current_fade_color
            np.write()
        else:
            is_fading = False
            for i in AVATAR_LED_MAP["head"]:
                np[i] = current_base_head_color
            np.write()

    # 6. EXECUTE PULSING (For the eyes)
    update_pulsing()

    # 7. UPDATE AUDIO METER (Display 2)
    update_audio_meter(current_avatar_state)

