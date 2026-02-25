# Updated Avatar Detection – tighter no-avatar window + debug voltage always shown
from machine import Pin, ADC
import neopixel
import time

NUM_LEDS = 7
NEO_PIN = 28
ADC_PIN = 26

np = neopixel.NeoPixel(Pin(NEO_PIN), NUM_LEDS)
adc = ADC(ADC_PIN)

# ─── Adjust these after measuring real voltages with new pull-down (aim for 2.2–4.7 kΩ) ───
NO_AVATAR_MAX   = 0.02     # very strict now
AV1_47K_MIN     = 0.70
AV1_47K_MAX     = 1.35
AV2_20K_MIN     = 1.36
AV2_20K_MAX     = 1.8     # leave headroom below 3.3 V

COLOR_OFF    = (0, 0, 0)
COLOR_AV1    = (0, 0, 220)    # blue
COLOR_AV2    = (220, 220, 0)  # yellow

def read_voltage(samples=8):
    total = 0
    for _ in range(samples):
        total += adc.read_u16()
        time.sleep(0.004)
    raw = total / samples
    return (raw / 65535) * 3.3

def set_color(color):
    for i in range(NUM_LEDS):
        np[i] = color
    np.write()

set_color(COLOR_OFF)
print("Started. Waiting for stable readings...")
print("47k = Avatar 1 → blue    |    20k = Avatar 2 → yellow    |    none → off")
print("-" * 60)

while True:
    v = read_voltage()
    print(f"Voltage: {v:5.3f} V   ", end=" → ")

    if v <= NO_AVATAR_MAX:
        set_color(COLOR_OFF)
        print("No avatar")
    elif AV1_47K_MIN <= v <= AV1_47K_MAX:
        set_color(COLOR_AV1)
        print("Avatar 1 (47 kΩ) – Blue")
    elif AV2_20K_MIN <= v <= AV2_20K_MAX:
        set_color(COLOR_AV2)
        print("Avatar 2 (20 kΩ) – Yellow")
    else:
        set_color(COLOR_OFF)
        print("OUT OF RANGE – possible noise / bad contact")

    time.sleep(0.4)
