import tkinter as tk

from mic_control import set_mic_mute
from lock_control import lock_os
from clipboard_control import wipe_clipboard_history
from usb_alert_control import toggle_usb_alert
from airplane import gui_toggle_airplane_mode


# ===== STATE =====

mic_is_muted = False
usb_alert_is_on = False
airplane_mode_is_on = False


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


# ===== GUI =====

root = tk.Tk()
root.title("PrivacyDeck Control")
root.geometry("320x410")
root.resizable(False, False)

title = tk.Label(root, text="PrivacyDeck GUI", font=("Arial", 14, "bold"))
title.pack(pady=10)


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


root.mainloop()
