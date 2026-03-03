import tkinter as tk
import threading
import time
import math
import struct

try:
    import sounddevice as sd
    import numpy as np
    _HAS_SOUNDEVICE = True
except Exception:
    sd = None
    np = None
    _HAS_SOUNDEVICE = False

try:
    import pyaudio
    _HAS_PYAUDIO = True
except Exception:
    pyaudio = None
    _HAS_PYAUDIO = False


class _LevelReader:
    def __init__(self, samplerate=44100, blocksize=1024):
        self.samplerate = samplerate
        self.blocksize = blocksize
        self._level = 0.0
        self._running = False
        self._thread = None
        self._stream = None

    @property
    def level(self):
        return self._level

    def start(self):
        if _HAS_SOUNDEVICE:
            self._start_sounddevice()
        elif _HAS_PYAUDIO:
            self._start_pyaudio()
        else:
            print(">> Audio meter: no supported audio backend (sounddevice or pyaudio)")
        self._running = True

    def stop(self):
        self._running = False
        try:
            if _HAS_SOUNDEVICE and self._stream is not None:
                self._stream.close()
                self._stream = None
        except Exception:
            pass

    # sounddevice implementation
    def _start_sounddevice(self):
        def callback(indata, frames, time_info, status):
            try:
                if status:
                    pass
                # compute RMS on channel 0
                rms = np.sqrt(np.mean(indata[:, 0].astype(np.float64) ** 2))
                self._level = float(rms)
            except Exception:
                pass

        try:
            self._stream = sd.InputStream(channels=1, samplerate=self.samplerate, blocksize=self.blocksize, callback=callback)
            self._stream.start()
            print(">> Audio meter: using sounddevice backend")
        except Exception as e:
            print(f">> sounddevice stream failed: {e}")

    # pyaudio fallback (reads in thread)
    def _start_pyaudio(self):
        def run_thread():
            pa = pyaudio.PyAudio()
            try:
                stream = pa.open(format=pyaudio.paInt16, channels=1, rate=self.samplerate, input=True, frames_per_buffer=self.blocksize)
            except Exception as e:
                print(f">> pyaudio open failed: {e}")
                return

            while self._running:
                try:
                    data = stream.read(self.blocksize, exception_on_overflow=False)
                    vals = struct.unpack(str(self.blocksize) + 'h', data)
                    # compute RMS
                    s = 0.0
                    for v in vals:
                        s += (v / 32768.0) ** 2
                    rms = math.sqrt(s / len(vals))
                    self._level = rms
                except Exception:
                    pass
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
            try:
                pa.terminate()
            except Exception:
                pass

        self._running = True
        self._thread = threading.Thread(target=run_thread, daemon=True)
        self._thread.start()
        print(">> Audio meter: using pyaudio backend")


class AudioMeterWidget(tk.Frame):
    def __init__(self, parent, width=80, height=160, update_ms=50, sensitivity=0.05):
        super().__init__(parent, width=width, height=height, bg="black")
        self.pack_propagate(False)
        self._width = width
        self._height = height
        self._canvas = tk.Canvas(self, width=width, height=height, bg="black", highlightthickness=0)
        self._canvas.pack()

        self._reader = _LevelReader()
        self._reader.start()

        self._update_ms = update_ms
        self._sensitivity = sensitivity
        self._bar = None
        self._after_job = None

        self._draw_static()
        self._schedule()

    def _draw_static(self):
        # draw border
        self._canvas.create_rectangle(0, 0, self._width, self._height, outline="#222", width=1)
        # initial bar
        self._bar = self._canvas.create_rectangle(2, self._height - 2, self._width - 2, self._height - 2, fill="#0f0", outline="")

    def _level_to_value(self, rms: float) -> float:
        # Convert RMS to normalized 0..1 using sensitivity
        v = float(rms) / max(1e-6, self._sensitivity)
        v = max(0.0, min(1.0, v))
        return v

    def _value_to_color(self, v: float) -> str:
        # green->yellow->red
        if v <= 0.5:
            t = v / 0.5
            r = int(255 * t)
            g = 255
        else:
            t = (v - 0.5) / 0.5
            r = 255
            g = int(255 * (1 - t))
        return f"#{r:02x}{g:02x}00"

    def _update_once(self):
        rms = self._reader.level
        v = self._level_to_value(rms)
        h = int(round(v * (self._height - 4)))
        y1 = self._height - 2 - h
        # update rectangle coords
        self._canvas.coords(self._bar, 2, y1, self._width - 2, self._height - 2)
        self._canvas.itemconfigure(self._bar, fill=self._value_to_color(v))

    def _schedule(self):
        self._update_once()
        self._after_job = self.after(self._update_ms, self._schedule)

    def stop(self):
        if self._after_job is not None:
            self.after_cancel(self._after_job)
            self._after_job = None
        try:
            self._reader.stop()
        except Exception:
            pass

    def set_sensitivity(self, sensitivity: float):
        self._sensitivity = max(1e-6, float(sensitivity))


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Audio Meter Test")
    meter = AudioMeterWidget(root)
    meter.pack(padx=10, pady=10)
    root.mainloop()
