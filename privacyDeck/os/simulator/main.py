import tkinter as tk
import threading
import time
import os
import json

import serial
from serial.tools import list_ports

from mic_control import set_mic_mute
from lock_control import lock_os
from clipboard_control import wipe_clipboard_history
from usb_alert_control import toggle_usb_alert
from airplane import gui_toggle_airplane_mode
from location import gui_toggle_location
from blackout import show_blackout_image
from webcam import WebcamController
from audio_meter import AudioMeterWidget


# ===== STATE =====

mic_is_muted = False
usb_alert_is_on = False
airplane_mode_is_on = False
location_is_on = False

SERIAL_PORT = os.getenv("PICO_SERIAL_PORT")
SERIAL_BAUDRATE = 115200

FUNCTION_TO_ACTION = {
    "Lock OS": "lock_system",
    "wipe clipboard history": "wipe_clipboard",
    "mic mute toggle": "toggle_mic",
    "airplane mode": "toggle_airplane",
    "blackout/presentation mode": "show_blackout",
    "usb alert": "toggle_usb",
    "browser clean": None,
    "gps mode": None,
    "Instant Privacy": None,
}


class PicoSerialListener:
    def __init__(self, port, baudrate, event_callback, status_callback):
        self.port = port
        self.baudrate = baudrate
        self.event_callback = event_callback
        self.status_callback = status_callback
        self._stop_event = threading.Event()
        self._serial = None
        self._thread = None

    def start(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run_listener, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass

    def _resolve_port(self):
        if self.port:
            return self.port

        for item in list_ports.comports():
            device = (item.device or "").lower()
            description = (item.description or "").lower()
            if "ttyacm" in device or "ttyusb" in device:
                return item.device
            if "pico" in description or "rp2040" in description:
                return item.device
        return None

    def _run_listener(self):
        self.status_callback("Serial: waiting for Pico...")
        while not self._stop_event.is_set():
            port = self._resolve_port()
            if not port:
                self.status_callback("Serial: no device found")
                time.sleep(2.0)
                continue

            try:
                ser = serial.Serial(port=port, baudrate=self.baudrate, timeout=1.0)
                self._serial = ser
                try:
                    ser.reset_input_buffer()
                except Exception:
                    pass
                self.status_callback(f"Serial: connected on {port}")

                while not self._stop_event.is_set():
                    raw = ser.readline()
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                        
                    if "function" not in data:
                        continue
                        
                    print(f"[SERIAL RX] {line}")
                    self._dispatch_event(data)
            except (serial.SerialException, OSError):
                self.status_callback("Serial: disconnected, retrying...")
                time.sleep(1.5)
            finally:
                if self._serial is not None:
                    try:
                        self._serial.close()
                    except Exception:
                        pass
                self._serial = None

        self.status_callback("Serial: stopped")

    def _dispatch_event(self, data):
        func = data.get("function")
        if func not in FUNCTION_TO_ACTION:
            print(f"[IGNORED] unknown function: {func}")
            return

        action = FUNCTION_TO_ACTION[func]
        if action is None:
            print(f"[IGNORED] no daemon action for: {func}")
            return

        print(f"[CALL] {action}")
        self.event_callback(action)


# ===== CALLBACKS =====

def toggle_mic():
    global mic_is_muted
    mic_is_muted = not mic_is_muted
    set_mic_mute(mic_is_muted)
    btn_toggle_mic.config(
        text=f"Toggle: Mic {'Muted' if mic_is_muted else 'Active'}"
    )


def lock_system():
    lock_os()


def wipe_clipboard():
    wipe_clipboard_history()


def show_blackout():
    show_blackout_image()


def toggle_usb():
    global usb_alert_is_on
    usb_alert_is_on = not usb_alert_is_on
    toggle_usb_alert(usb_alert_is_on)
    btn_toggle_usb.config(
        text=f"Toggle: USB Alert {'ON' if usb_alert_is_on else 'OFF'}"
    )


def toggle_airplane_mode():
    global airplane_mode_is_on
    success = gui_toggle_airplane_mode()
    if success:
        airplane_mode_is_on = not airplane_mode_is_on

    btn_toggle_airplane.config(
        text=f"Toggle: Airplane Mode {'ON' if airplane_mode_is_on else 'OFF'}"
    )


def toggle_location():
    global location_is_on
    success = gui_toggle_location()
    if success:
        location_is_on = not location_is_on

    btn_toggle_location.config(
        text=f"Toggle: Location {'ON' if location_is_on else 'OFF'}"
    )


def set_webcam_privacy(value):
    webcam_controller.set_privacy_level(value)


def update_network_status(text):
    root.after(0, lambda: network_status_label.config(text=text))


def handle_network_event(event_name):
    if event_name == "lock_system":
        root.after(0, lock_system)
    elif event_name == "wipe_clipboard":
        root.after(0, wipe_clipboard)
    elif event_name == "toggle_usb":
        root.after(0, toggle_usb)
    elif event_name == "toggle_airplane":
        root.after(0, toggle_airplane_mode)
    elif event_name == "show_blackout":
        root.after(0, show_blackout)
    elif event_name == "toggle_mic":
        root.after(0, toggle_mic)


def on_close():
    serial_listener.stop()
    webcam_controller.stop()
    try:
        audio_meter.stop()
    except Exception:
        pass
    root.destroy()


# ===== GUI =====

root = tk.Tk()
root.title("PrivacyDeck Control")
root.geometry("320x760")
root.resizable(False, False)

title = tk.Label(root, text="PrivacyDeck GUI", font=("Arial", 14, "bold"))
title.pack(pady=10)

network_status_label = tk.Label(root, text="Serial: starting...")
network_status_label.pack(pady=(0, 6))

# place webcam and audio meter side-by-side
top_row = tk.Frame(root)
top_row.pack(pady=6)

webcam_controller = WebcamController(top_row)
# re-pack webcam frame to the left and add audio meter
try:
    webcam_controller._frame.pack_forget()
except Exception:
    pass
webcam_controller._frame.pack(side="left", padx=(0, 6))

audio_meter = AudioMeterWidget(top_row, width=80, height=160)
audio_meter.pack(side="left")

serial_listener = PicoSerialListener(
    port=SERIAL_PORT,
    baudrate=SERIAL_BAUDRATE,
    event_callback=handle_network_event,
    status_callback=update_network_status,
)
serial_listener.start()


# ===== TOGGLE SECTION =====

label_toggle = tk.Label(root, text="Toggle:")
label_toggle.pack()

btn_toggle_mic = tk.Button(
    root,
    text="Toggle: Mic Active",
    width=22,
    height=2,
    command=toggle_mic
)
btn_toggle_mic.pack(pady=5)

btn_toggle_usb = tk.Button(
    root,
    text="Toggle: USB Alert OFF",
    width=22,
    height=2,
    command=toggle_usb
)
btn_toggle_usb.pack(pady=5)

btn_toggle_airplane = tk.Button(
    root,
    text="Toggle: Airplane Mode OFF",
    width=22,
    height=2,
    command=toggle_airplane_mode
)
btn_toggle_airplane.pack(pady=5)

btn_toggle_location = tk.Button(
    root,
    text="Toggle: Location OFF",
    width=22,
    height=2,
    command=toggle_location
)
btn_toggle_location.pack(pady=5)

label_webcam = tk.Label(root, text="Webcam Privacy Slider")
label_webcam.pack(pady=(4, 0))

slider_webcam = tk.Scale(
    root,
    from_=0,
    to=100,
    orient="horizontal",
    length=220,
    command=set_webcam_privacy
)
slider_webcam.set(0)
slider_webcam.pack(pady=(0, 8))
set_webcam_privacy(0)


# ===== BUTTON SECTION =====

label_button = tk.Label(root, text="Button:")
label_button.pack(pady=(10, 0))

btn_lock = tk.Button(
    root,
    text="Button: Lock OS",
    width=22,
    height=2,
    command=lock_system
)
btn_lock.pack(pady=5)

btn_clipboard = tk.Button(
    root,
    text="Button: Wipe Clipboard History",
    width=22,
    height=2,
    command=wipe_clipboard
)
btn_clipboard.pack(pady=5)

btn_blackout = tk.Button(
    root,
    text="Button: Blackout",
    width=22,
    height=2,
    command=show_blackout
)
btn_blackout.pack(pady=5)


root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
