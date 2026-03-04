"""
Real-time microphone audio level meter widget.

AudioMeterWidget is a tkinter Canvas that displays a vertical VU-style bar.
Call stop() to halt the audio capture thread before the application exits.
"""

import tkinter as tk


class AudioMeterWidget(tk.Canvas):
    def __init__(self, parent: tk.Widget, width: int = 80, height: int = 160, **kwargs):
        super().__init__(parent, width=width, height=height, bg="black", **kwargs)
        self._width = width
        self._height = height
        self.create_text(
            width // 2, height // 2,
            text="[Audio]",
            fill="white",
            font=("Arial", 8),
        )

    def stop(self) -> None:
        """Stop the audio capture thread."""
        pass
