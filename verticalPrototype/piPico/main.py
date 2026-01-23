from machine import Pin
import time
import sys

# Pins
lock_button = Pin(14, Pin.IN, Pin.PULL_UP)
mic_toggle  = Pin(15, Pin.IN, Pin.PULL_UP)
led         = Pin(16, Pin.OUT)

last_lock_state = lock_button.value()
last_mic_state  = mic_toggle.value()

print("PICO_READY")

def send(msg):
    print(msg)   # KEIN flush() in MicroPython

while True:
    # ---- LOCK BUTTON ----
    current_lock = lock_button.value()
    if last_lock_state == 1 and current_lock == 0:
        send("LOCK_OS")
        time.sleep(0.3)  # Debounce
    last_lock_state = current_lock

    # ---- MIC TOGGLE ----
    current_mic = mic_toggle.value()
    if current_mic != last_mic_state:
        if current_mic == 0:
            send("MIC_MUTED")
            led.on()
        else:
            send("MIC_UNMUTED")
            led.off()
        last_mic_state = current_mic
        time.sleep(0.1)

    time.sleep(0.01)


