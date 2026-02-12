import tkinter as tk

from mic_control import set_mic_mute
from lock_control import lock_os


# ===== STATE =====

mic_is_muted = False   # Toggle Zustand


# ===== CALLBACKS =====

def toggle_mic():
    global mic_is_muted

    mic_is_muted = not mic_is_muted
    set_mic_mute(mic_is_muted)

    # Button Text updaten (optional nice UX)
    if mic_is_muted:
        btn_toggle_mic.config(text="Toggle: Mic Muted")
    else:
        btn_toggle_mic.config(text="Toggle: Mic Active")


def lock_system():
    lock_os()


# ===== GUI =====

root = tk.Tk()
root.title("PrivacyDeck Control")
root.geometry("320x220")
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


root.mainloop()
