import tkinter as tk

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


def on_close():
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
