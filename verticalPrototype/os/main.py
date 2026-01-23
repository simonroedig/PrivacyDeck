import serial
import platform
import time
import os
import subprocess

# Betriebssystem erkennen
OS_TYPE = platform.system() 

# Windows-spezifische Imports (nur laden, wenn nötig)
if OS_TYPE == "Windows":
    import comtypes
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# ===== FUNKTIONEN FÜR DAS MIKROFON =====

def set_mic_mute(mute_state: bool):
    """
    Stummschaltung basierend auf dem Betriebssystem.
    mute_state: True für Mute, False für Unmute
    """
    if OS_TYPE == "Windows":
        try:
            comtypes.CoInitialize()
            interface = AudioUtilities.GetMicrophone().Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            mic = cast(interface, POINTER(IAudioEndpointVolume))
            mic.SetMute(1 if mute_state else 0, None)
            print(f">> Windows: Mikro {'STUMM' if mute_state else 'AKTIV'}")
        except Exception as e:
            print(f"Windows Audio Fehler: {e}")
        finally:
            comtypes.CoUninitialize()
            
    elif OS_TYPE == "Linux":
        # amixer Befehl für Linux (Zorin OS / Ubuntu)
        cmd = "nocap" if mute_state else "cap"
        os.system(f"amixer set Capture {cmd}")
        print(f">> Linux: Mikro {'STUMM' if mute_state else 'AKTIV'} (via amixer)")

# ===== FUNKTION FÜR DEN LOCK-SCREEN =====

def lock_os():
    """Sperrt den Bildschirm basierend auf dem Betriebssystem."""
    if OS_TYPE == "Windows":
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif OS_TYPE == "Linux":
        # Funktioniert unter Zorin/Gnome und den meisten anderen Linux Desktops
        os.system("xdg-screensaver lock")
    print(f">> {OS_TYPE}: System gesperrt")

# ===== SETUP SERIELLER PORT =====

# Port-Automatik: Windows nutzt COM, Linux nutzt /dev/tty...
if OS_TYPE == "Windows":
    PORT = "COM10"
else:
    # Standard-Port für Pico unter Linux (ggf. prüfen mit 'ls /dev/ttyACM*')
    PORT = "/dev/ttyACM0" 

BAUD = 115200

print(f"--- PrivacyDeck Daemon gestartet auf {OS_TYPE} ---")
print(f"Verbinde mit Port: {PORT}...")

try:
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    print("Verbindung erfolgreich!")
except Exception as e:
    print(f"FEHLER: Port {PORT} konnte nicht geöffnet werden.")
    print("Tipp: Unter Linux musst du evtl. 'sudo usermod -aG dialout $USER' ausführen.")
    exit()

# ===== MAIN LOOP =====

while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        if not line:
            continue

        print(f"Signal vom Pico: {line}")

        if line == "LOCK_OS":
            lock_os()

        elif line == "MIC_MUTED":
            set_mic_mute(True)

        elif line == "MIC_UNMUTED":
            set_mic_mute(False)

    except Exception as e:
        print(f"Fehler im Loop: {e}")
        time.sleep(1)