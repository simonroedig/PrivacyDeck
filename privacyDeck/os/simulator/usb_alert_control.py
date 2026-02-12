import platform
import threading
import time
import os
import ctypes
import subprocess

OS_TYPE = platform.system()

# Globaler Toggle-State
usb_alert_active = False

# Speicherung aktueller Devices zum Vergleich
known_devices = set()

# Thread-Steuerung
monitor_thread = None
stop_event = threading.Event()

# Optionaler Toast-Notifier (Windows)
toast_notifier = None


# ===== HELPER: OS-Popup =====

def show_popup(message: str):
    global toast_notifier
    try:
        if OS_TYPE == "Windows":
            # Windows Toast, Fallback auf native MessageBox
            try:
                if toast_notifier is None:
                    from win10toast import ToastNotifier
                    toast_notifier = ToastNotifier()
                toast_notifier.show_toast("PrivacyDeck Alert", message, duration=5, threaded=True)
            except Exception:
                ctypes.windll.user32.MessageBoxW(0, message, "PrivacyDeck Alert", 0x40)

        elif OS_TYPE == "Linux":
            # notify-send
            subprocess.run(["notify-send", "PrivacyDeck Alert", message], check=False)

        elif OS_TYPE == "Darwin":
            # macOS AppleScript
            subprocess.run(
                ["osascript", "-e", f'display notification "{message}" with title "PrivacyDeck Alert"'],
                check=False
            )

        else:
            print(f">> {OS_TYPE}: {message}")

    except Exception as e:
        print(f"Popup Fehler: {e}")


# ===== HELPER: Liste der USB Devices =====

def get_current_usb_devices():
    devices = set()
    try:
        if OS_TYPE == "Windows":
            # Alle aktuell präsenten USB PnP-Geräte (nicht nur USB-Sticks)
            try:
                import wmi
                c = wmi.WMI()
                for dev in c.Win32_PnPEntity():
                    pnp_id = getattr(dev, "PNPDeviceID", None)
                    if pnp_id and pnp_id.upper().startswith("USB"):
                        name = getattr(dev, "Name", None) or getattr(dev, "Caption", None) or "Unknown USB device"
                        devices.add(f"{name} | {pnp_id}")
            except Exception:
                # Fallback über PowerShell, falls wmi nicht verfügbar ist
                result = subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        "Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -like 'USB*' } | "
                        "ForEach-Object { \"$($_.FriendlyName) | $($_.InstanceId)\" }"
                    ],
                    capture_output=True,
                    text=True,
                    check=False
                )
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line:
                        devices.add(line)

        elif OS_TYPE == "Linux":
            output = subprocess.run(["lsusb"], capture_output=True, text=True, check=False).stdout
            for line in output.splitlines():
                line = line.strip()
                if line:
                    devices.add(line)

        elif OS_TYPE == "Darwin":
            output = subprocess.run(
                ["system_profiler", "SPUSBDataType", "-detailLevel", "mini"],
                capture_output=True,
                text=True,
                check=False
            ).stdout
            for line in output.splitlines():
                line = line.strip()
                if line:
                    devices.add(line)
    except Exception as e:
        print(f"Fehler beim Lesen von USB Devices: {e}")
    return devices


# ===== MONITORING THREAD =====

def usb_monitor_loop():
    global known_devices
    known_devices = get_current_usb_devices()

    while not stop_event.is_set():
        # Polling alle 2 Sekunden, aber sofort stoppbar
        if stop_event.wait(2):
            break
        current = get_current_usb_devices()
        new_devices = current - known_devices

        if new_devices:
            for dev in new_devices:
                show_popup(f"Attention: New USB device detected ({dev}). Please ensure you intend to use it.")
        known_devices = current


# ===== API: Toggle Funktion =====

def toggle_usb_alert(active: bool):
    global usb_alert_active, monitor_thread

    # Keine Doppel-Threads starten
    if active == usb_alert_active:
        print(f">> USB Alert already {'activated' if active else 'deactivated'}")
        return

    usb_alert_active = active

    if active:
        stop_event.clear()
        monitor_thread = threading.Thread(target=usb_monitor_loop, daemon=True)
        monitor_thread.start()
        print(">> USB Alert activated")
    else:
        stop_event.set()
        print(">> USB Alert deactivated")
