import tkinter as tk
import socket
import threading

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

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 50555


class PicoNetworkServer:
    def __init__(self, host, port, event_callback, status_callback):
        self.host = host
        self.port = port
        self.event_callback = event_callback
        self.status_callback = status_callback
        self._stop_event = threading.Event()
        self._server_socket = None
        self._accept_thread = None

    def start(self):
        if self._accept_thread is not None:
            return
        self._accept_thread = threading.Thread(target=self._run_server, daemon=True)
        self._accept_thread.start()

    def stop(self):
        self._stop_event.set()
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass

    def _run_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket = server_socket
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(2)
        server_socket.settimeout(1.0)
        self.status_callback(f"Network: listening on {self.host}:{self.port}")

        while not self._stop_event.is_set():
            try:
                conn, addr = server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            client_thread = threading.Thread(
                target=self._handle_client,
                args=(conn, addr),
                daemon=True,
            )
            client_thread.start()

        self.status_callback("Network: stopped")

    def _send_line(self, conn, message):
        conn.sendall((message + "\n").encode("utf-8"))

    def _read_line(self, conn):
        data = bytearray()
        while True:
            chunk = conn.recv(1)
            if not chunk:
                return None
            if chunk == b"\n":
                break
            data.extend(chunk)
        return data.decode("utf-8", errors="replace").strip()

    def _handle_client(self, conn, addr):
        conn.settimeout(30.0)
        self.status_callback(f"Network: connection from {addr[0]}:{addr[1]}")
        try:
            hello = self._read_line(conn)
            if hello != "HELLO PRIVACYDECK_PICO 1":
                self._send_line(conn, "ERR handshake")
                return

            self._send_line(conn, "HELLO_ACK PRIVACYDECK_DAEMON 1")
            self.status_callback(f"Network: connected to {addr[0]}:{addr[1]}")

            while not self._stop_event.is_set():
                line = self._read_line(conn)
                if line is None:
                    break

                if line == "PING":
                    self._send_line(conn, "PONG")
                    continue

                if line == "EVENT LOCK_BUTTON pressed":
                    self.event_callback("lock_system")
                    self._send_line(conn, "OK")
                    continue

                self._send_line(conn, "ERR unknown_event")
        except (ConnectionError, OSError):
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass
            self.status_callback("Network: waiting for device")


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


def on_close():
    network_server.stop()
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

network_status_label = tk.Label(root, text="Network: starting...")
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

network_server = PicoNetworkServer(
    host=SERVER_HOST,
    port=SERVER_PORT,
    event_callback=handle_network_event,
    status_callback=update_network_status,
)
network_server.start()


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
