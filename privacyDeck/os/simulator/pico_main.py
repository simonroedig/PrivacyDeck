import machine
import time
import json

# Define push buttons (trigger only on press)
BUTTONS = {
    0: {"name": "Button 1", "func": "Lock OS"},
    1: {"name": "Button 2", "func": "browser clean"},
    2: {"name": "Button 3", "func": "gps mode"},
    3: {"name": "Button 4", "func": "wipe clipboard history"},
    4: {"name": "Button 5", "func": "Instant Privacy"}
}

# Define toggle switches (trigger on any state change)
# Swapped Toggle 1 and Toggle 4 functions as requested
TOGGLES = {
    5: {"name": "Toggle 1", "func": "usb alert"},
    6: {"name": "Toggle 2", "func": "blackout/presentation mode"},
    7: {"name": "Toggle 3", "func": "airplane mode"},
    8: {"name": "Toggle 4", "func": "mic mute toggle"}
}

# Initialization and state tracking
pins = {}
last_states = {}
last_debounce_time = {}
DEBOUNCE_DELAY = 50  # 50 milliseconds to prevent switch bouncing

# Setup all pins with internal Pull-Ups
for pin_num in list(BUTTONS.keys()) + list(TOGGLES.keys()):
    pin = machine.Pin(pin_num, machine.Pin.IN, machine.Pin.PULL_UP)
    pins[pin_num] = pin
    last_states[pin_num] = pin.value()
    last_debounce_time[pin_num] = 0

def send_serial(component_type, pin_num, name, func, state):
    """Formats the event as JSON and prints it to the serial output"""
    data = {
        "type": component_type,
        "pin": pin_num,
        "name": name,
        "function": func,
        "state": state
    }
    # print() in MicroPython automatically sends to the USB Serial port
    print(json.dumps(data))

print(json.dumps({"info": "Pico Macro Pad Started"}))

# Main loop
while True:
    current_time = time.ticks_ms()

    # --- Check Push Buttons ---
    for pin_num in BUTTONS.keys():
        current_value = pins[pin_num].value()
        
        # If the state changed
        if current_value != last_states[pin_num]:
            # Check if enough time has passed (debounce)
            if time.ticks_diff(current_time, last_debounce_time[pin_num]) > DEBOUNCE_DELAY:
                # 0 means pressed (connected to ground)
                if current_value == 0: 
                    send_serial("button", pin_num, BUTTONS[pin_num]["name"], BUTTONS[pin_num]["func"], "pressed")
                
                last_states[pin_num] = current_value
                last_debounce_time[pin_num] = current_time

    # --- Check Toggles ---
    for pin_num in TOGGLES.keys():
        current_value = pins[pin_num].value()
        
        # If the toggle state changed
        if current_value != last_states[pin_num]:
            # Check if enough time has passed (debounce)
            if time.ticks_diff(current_time, last_debounce_time[pin_num]) > DEBOUNCE_DELAY:
                # 0 usually means switch is ON (closed to ground), 1 means OFF (open)
                state_str = "ON" if current_value == 0 else "OFF"
                send_serial("toggle", pin_num, TOGGLES[pin_num]["name"], TOGGLES[pin_num]["func"], state_str)
                
                last_states[pin_num] = current_value
                last_debounce_time[pin_num] = current_time
