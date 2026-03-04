"""
Webcam live-preview widget with a privacy-level slider.

WebcamController wraps a tkinter Frame that contains a live camera feed.
Call set_privacy_level(0–100) to apply blur / overlay; 0 = clear, 100 = fully hidden.
Call stop() to release the camera before the application exits.
"""

import tkinter as tk


class WebcamController:
    def __init__(self, parent: tk.Widget):
        self._frame = tk.Frame(parent, width=220, height=160, bg="black")
        self._label = tk.Label(self._frame, text="[Camera]", fg="white", bg="black")
        self._label.pack(expand=True)
        self._frame.pack()

    def set_privacy_level(self, level) -> None:
        """Apply a privacy overlay.  level: 0 (clear) – 100 (fully opaque)."""
        raise NotImplementedError("set_privacy_level() is not implemented")

    def stop(self) -> None:
        """Release the camera capture resource."""
        pass
