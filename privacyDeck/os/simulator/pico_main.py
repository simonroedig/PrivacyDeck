import machine
from machine import Pin, ADC, SPI
import time
import json
import neopixel
import ST7735

# --- Color Definitions (RGB565) ---
RED    = 0xF800
BLACK  = 0x0000

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
# AVATAR & DISPLAY CONFIGURATION
# ==========================================
NUM_LEDS = 7
NEO_PIN = 28
ADC_PIN = 26

# Thresholds
NO_AVATAR_MAX   = 0.69
AV1_47K_MIN     = 0.70
AV1_47K_MAX     = 1.35
AV2_20K_MIN     = 1.36
AV2_20K_MAX     = 1.8 

COLOR_OFF    = (0, 0, 0)
COLOR_AV1    = (0, 0, 220)    # blue
COLOR_AV2    = (220, 220, 0)  # yellow

# SPI Display 1 (Red / Webcam) - Using positional arguments to fix TypeError
spi1 = SPI(1, baudrate=20_000_000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11))
display1 = ST7735.TFT(spi1, Pin(12), Pin(13), Pin(9)) # Order: SPI, DC, RST, CS
display1.initr()

# SPI Display 2 (Blue / Mic)
spi0 = SPI(0, baudrate=20_000_000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19))
display2 = ST7735.TFT(spi0, Pin(20), Pin(21), Pin(17)) # Order: SPI, DC, RST, CS
display2.initr()
display2.fill(BLACK) 

# ==========================================
# HELPER FUNCTIONS
# ==========================================
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
        display.fill(RED) # Fallback if file is missing

def set_color(color):
    for i in range(NUM_LEDS):
        np[i] = color
    np.write()

def send_serial(component_type, pin_num, name, func, state):
    data = {"type": component_type, "pin": pin_num, "name": name, "function": func, "state": state}
    print(json.dumps(data))

# ==========================================
# INITIALIZATION
# ==========================================
pins = {}
last_states = {}
last_debounce_time = {}

for pin_num in list(BUTTONS.keys()) + list(TOGGLES.keys()):
    pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
    pins[pin_num] = pin
    last_states[pin_num] = pin.value()
    last_debounce_time[pin_num] = 0

np = neopixel.NeoPixel(Pin(NEO_PIN), NUM_LEDS)
adc = ADC(ADC_PIN)

set_color(COLOR_OFF)
display1.fill(RED) 
print(json.dumps({"info": "Pico Macro Pad & Displays Started"}))

# Main Loop Variables
voltage_samples = []
last_adc_read_time = 0
last_avatar_eval_time = 0
current_avatar_state = "none"

ADC_SAMPLE_INTERVAL = 4    
AVATAR_EVAL_INTERVAL = 400 

# ==========================================
# MAIN LOOP
# ==========================================
while True:
    current_time = time.ticks_ms()

    # 1. CHECK PUSH BUTTONS
    for pin_num in BUTTONS.keys():
        current_value = pins[pin_num].value()
        if current_value != last_states[pin_num]:
            if time.ticks_diff(current_time, last_debounce_time[pin_num]) > DEBOUNCE_DELAY:
                if current_value == 0: 
                    send_serial("button", pin_num, BUTTONS[pin_num]["name"], BUTTONS[pin_num]["func"], "pressed")
                last_states[pin_num] = current_value
                last_debounce_time[pin_num] = current_time

    # 2. CHECK TOGGLES
    for pin_num in TOGGLES.keys():
        current_value = pins[pin_num].value()
        if current_value != last_states[pin_num]:
            if time.ticks_diff(current_time, last_debounce_time[pin_num]) > DEBOUNCE_DELAY:
                state_str = "ON" if current_value == 0 else "OFF"
                send_serial("toggle", pin_num, TOGGLES[pin_num]["name"], TOGGLES[pin_num]["func"], state_str)
                last_states[pin_num] = current_value
                last_debounce_time[pin_num] = current_time

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
            new_color = COLOR_OFF
            
            if v <= NO_AVATAR_MAX:
                new_state = "none"
                print("no av")
                new_color = COLOR_OFF
            elif AV1_47K_MIN <= v <= AV1_47K_MAX:
                new_state = "av1"
                print("av1")
                new_color = COLOR_AV1
            elif AV2_20K_MIN <= v <= AV2_20K_MAX:
                new_state = "av2"
                print("av2")
                new_color = COLOR_AV2
            else:
                new_state = "none"
                print("no av")
                new_color = COLOR_OFF

            # EXECUTE CHANGE
            if new_state != current_avatar_state:
                set_color(new_color)
                
                if new_state == "av1":
                    draw_bin(display1, "avatar1_fullcamera.bin")
                elif new_state == "av2":
                    draw_bin(display1, "avatar2_fullcamera.bin")
                else:
                    display1.fill(RED)
                
                current_avatar_state = new_state
            
        last_avatar_eval_time = current_time
