import keyboard
import comtypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

def get_microphone():
    """Findet das Standard-Mikrofon."""
    # Wir nutzen hier direkt die Aktivierung
    interface = AudioUtilities.GetMicrophone().Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))

def mute_mic():
    try:
        # WICHTIG: Initialisiert COM für diesen Thread
        comtypes.CoInitialize()
        mic = get_microphone()
        mic.SetMute(1, None)
        print(">> Mikrofon STUMM (Muted)")
    except Exception as e:
        print(f"Fehler: {e}")
    finally:
        # COM wieder freigeben
        comtypes.CoUninitialize()

def unmute_mic():
    try:
        comtypes.CoInitialize()
        mic = get_microphone()
        mic.SetMute(0, None)
        print(">> Mikrofon AKTIV (Unmuted)")
    except Exception as e:
        print(f"Fehler: {e}")
    finally:
        comtypes.CoUninitialize()

print("--- Mikrofon Controller läuft ---")
print("Drücke 'Q' zum Stummschalten")
print("Drücke 'W' zum Aktivieren")
print("Drücke 'ESC' zum Beenden")

# Hotkeys registrieren
keyboard.add_hotkey('q', mute_mic)
keyboard.add_hotkey('w', unmute_mic)

# Script am Laufen halten
keyboard.wait('esc')