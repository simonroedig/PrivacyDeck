import platform
import os

OS_TYPE = platform.system()

# Windows Imports nur laden wenn nötig
if OS_TYPE == "Windows":
    import comtypes
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


def set_mic_mute(mute_state: bool):
    """
    True  = Mikro stumm
    False = Mikro aktiv
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
        cmd = "nocap" if mute_state else "cap"
        os.system(f"amixer set Capture {cmd}")
        print(f">> Linux: Mikro {'STUMM' if mute_state else 'AKTIV'}")
