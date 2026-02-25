from machine import Pin, ADC
import time

# -------------------------
# CONFIGURATION
# -------------------------

# Toggles (active LOW)
toggles = {
    "Mic Control": Pin(5, Pin.IN, Pin.PULL_UP),
    "Blackout / Presentation Mode": Pin(6, Pin.IN, Pin.PULL_UP),
    "Airplane Mode": Pin(7, Pin.IN, Pin.PULL_UP),
    "USB Alert Mic Control (Mute/Unmute)": Pin(8, Pin.IN, Pin.PULL_UP),
}

# Buttons (active LOW)
buttons = {
    "Lock OS": Pin(0, Pin.IN, Pin.PULL_UP),
    "Wipe Clipboard History": Pin(1, Pin.IN, Pin.PULL_UP),
    "Browser Clean Switch": Pin(2, Pin.IN, Pin.PULL_UP),
    "GPS Disable / Blackout Mode": Pin(3, Pin.IN, Pin.PULL_UP),
    "Instant Privacy": Pin(4, Pin.IN, Pin.PULL_UP),
}

# Linear slider (ADC on GPIO 27 = ADC1)
slider = ADC(27)

# Store previous states
toggle_states = {}
button_states = {}
last_slider_value = -1


# -------------------------
# INITIALIZE STATES
# -------------------------
for name, pin in toggles.items():
    toggle_states[name] = pin.value()

for name, pin in buttons.items():
    button_states[name] = pin.value()


print("=== Hardware Test Started ===")
print("Buttons and toggles are ACTIVE-LOW (connected to GND)")
print("--------------------------------\n")


# -------------------------
# MAIN LOOP
# -------------------------
while True:

    # Check toggles
    for name, pin in toggles.items():
        current = pin.value()
        if current != toggle_states[name]:
            toggle_states[name] = current
            if current == 0:
                print(f"[TOGGLE ON]  {name}")
            else:
                print(f"[TOGGLE OFF] {name}")

    # Check buttons
    for name, pin in buttons.items():
        current = pin.value()
        if current != button_states[name]:
            button_states[name] = current
            if current == 0:
                print(f"[BUTTON PRESSED]  {name}")
            else:
                print(f"[BUTTON RELEASED] {name}")

    # Read slider (0–65535)
    slider_value = slider.read_u16()

    # Only print if it changes significantly (avoid spam)
    if abs(slider_value - last_slider_value) > 2000:
        percent = (slider_value / 65535) * 100
        print(f"[SLIDER] Value: {slider_value} ({percent:.1f}%)")
        last_slider_value = slider_value

    time.sleep(0.05)
